"""Payment and subscription API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer
import structlog
from typing import Dict, Any
import json

from app.services.razorpay_service import get_razorpay_service, RazorpayService
from app.services.auth_service import get_current_user
from app.models.subscription import (
    PaymentLinkRequest, 
    PaymentLinkResponse,
    SubscriptionUpgradeRequest,
    SubscriptionCancellationRequest,
    WebhookEvent,
    WebhookProcessingResult,
    SubscriptionDetails
)
from app.models.core import SubscriptionTier
from app.repositories.subscriptions import get_subscriptions_repository

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
security = HTTPBearer()


@router.post("/create-payment-link", response_model=PaymentLinkResponse)
async def create_payment_link(
    request: PaymentLinkRequest,
    current_user: dict = Depends(get_current_user),
    razorpay_service: RazorpayService = Depends(get_razorpay_service)
):
    """Create a payment link for subscription upgrade."""
    try:
        if not razorpay_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Payment processing is currently unavailable"
            )
        
        # Create payment link
        payment_link = await razorpay_service.create_payment_link(
            tier=request.tier,
            user_id=current_user["id"],
            customer_email=current_user.get("email", request.customer_email),
            customer_name=request.customer_name
        )
        
        logger.info(
            "Created payment link",
            user_id=current_user["id"],
            tier=request.tier.value,
            payment_link_id=payment_link["id"]
        )
        
        return PaymentLinkResponse(
            payment_link_id=payment_link["id"],
            payment_url=payment_link["short_url"],
            amount=payment_link["amount"] / 100,  # Convert from paise
            tier=request.tier,
            expires_at=payment_link.get("expire_by"),
            created_at=payment_link["created_at"]
        )
        
    except Exception as e:
        logger.error("Failed to create payment link", error=str(e), user_id=current_user["id"])
        raise HTTPException(status_code=500, detail="Failed to create payment link")


@router.post("/upgrade-subscription")
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: dict = Depends(get_current_user),
    razorpay_service: RazorpayService = Depends(get_razorpay_service)
):
    """Initiate subscription upgrade process."""
    try:
        if request.target_tier == SubscriptionTier.FREE:
            raise HTTPException(
                status_code=400,
                detail="Cannot upgrade to free tier"
            )
        
        # For now, return payment link creation instructions
        # In a full implementation, this would check current tier and create appropriate payment
        return {
            "message": "Use create-payment-link endpoint to generate payment for upgrade",
            "target_tier": request.target_tier.value,
            "next_step": "create_payment_link"
        }
        
    except Exception as e:
        logger.error("Failed to upgrade subscription", error=str(e), user_id=current_user["id"])
        raise HTTPException(status_code=500, detail="Failed to process upgrade request")


@router.post("/cancel-subscription")
async def cancel_subscription(
    request: SubscriptionCancellationRequest,
    current_user: dict = Depends(get_current_user),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    subscription_repo = Depends(get_subscriptions_repository)
):
    """Cancel user subscription."""
    try:
        # Get current subscription
        subscription = await subscription_repo.get_by_user_id(current_user["id"])
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        if subscription.tier == SubscriptionTier.FREE:
            raise HTTPException(status_code=400, detail="Cannot cancel free tier")
        
        # Cancel in Razorpay if subscription exists
        if subscription.razorpay_subscription_id:
            await razorpay_service.cancel_subscription(subscription.razorpay_subscription_id)
        
        # Update local subscription status
        await subscription_repo.cancel_subscription(
            subscription.id, 
            reason=request.reason,
            immediate=request.cancel_immediately
        )
        
        logger.info(
            "Cancelled subscription",
            user_id=current_user["id"],
            subscription_id=subscription.id,
            immediate=request.cancel_immediately
        )
        
        return {
            "message": "Subscription cancelled successfully",
            "cancelled_immediately": request.cancel_immediately,
            "effective_date": "immediate" if request.cancel_immediately else "end_of_billing_cycle"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel subscription", error=str(e), user_id=current_user["id"])
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/subscription-details", response_model=SubscriptionDetails)
async def get_subscription_details(
    current_user: dict = Depends(get_current_user),
    subscription_repo = Depends(get_subscriptions_repository)
):
    """Get detailed subscription information for current user."""
    try:
        subscription = await subscription_repo.get_by_user_id(current_user["id"])
        if not subscription:
            raise HTTPException(status_code=404, detail="No subscription found")
        
        # Convert to detailed response model
        return SubscriptionDetails(
            id=subscription.id,
            user_id=subscription.user_id,
            tier=subscription.tier,
            status="active" if subscription.is_active else "inactive",
            razorpay_subscription_id=subscription.razorpay_subscription_id,
            razorpay_customer_id=subscription.razorpay_customer_id,
            current_period_start=subscription.subscription_start_date,
            current_period_end=subscription.subscription_end_date,
            amount=0 if subscription.tier == SubscriptionTier.FREE else 50 if subscription.tier == SubscriptionTier.PRO else 500,
            api_key=subscription.api_key_hash,
            webhook_url=subscription.webhook_url,
            alert_thresholds=subscription.alert_thresholds,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get subscription details", error=str(e), user_id=current_user["id"])
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription details")


@router.post("/webhook", response_model=WebhookProcessingResult)
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    razorpay_service: RazorpayService = Depends(get_razorpay_service)
):
    """Handle Razorpay webhook events."""
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature", "")
        
        # Verify webhook signature
        if not await razorpay_service.verify_webhook_signature(body, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse webhook data
        try:
            webhook_data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Process webhook in background
        background_tasks.add_task(
            process_webhook_background,
            webhook_data,
            razorpay_service
        )
        
        # Return immediate response
        return WebhookProcessingResult(
            event_type=webhook_data.get("event", "unknown"),
            processed=True,
            action="queued_for_processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def process_webhook_background(
    webhook_data: Dict[str, Any],
    razorpay_service: RazorpayService
):
    """Process webhook event in background task."""
    try:
        result = await razorpay_service.process_webhook_event(webhook_data)
        
        # Here you would typically update the database based on the webhook result
        # For now, just log the result
        logger.info("Processed webhook event", result=result)
        
        # TODO: Update subscription status in database based on result
        # if result.get("user_id") and result.get("action"):
        #     await update_subscription_from_webhook(result)
        
    except Exception as e:
        logger.error("Background webhook processing failed", error=str(e))


@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans."""
    from app.config import get_settings
    settings = get_settings()
    
    plans = []
    for tier_name, config in settings.subscription_tiers.items():
        plans.append({
            "tier": tier_name,
            "name": f"ZERO-COMP {tier_name.title()}",
            "price": config["price"],
            "features": config["features"],
            "rate_limits": config["rate_limits"]
        })
    
    return {"plans": plans}


@router.get("/health")
async def payment_health_check(
    razorpay_service: RazorpayService = Depends(get_razorpay_service)
):
    """Health check for payment service."""
    return {
        "status": "healthy",
        "razorpay_configured": razorpay_service.is_configured(),
        "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
    }