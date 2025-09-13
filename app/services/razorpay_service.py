"""Razorpay payment processing service."""

import razorpay
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog
from app.config import get_settings
from app.models.subscription import SubscriptionTier, PaymentStatus, SubscriptionStatus

logger = structlog.get_logger(__name__)


class RazorpayService:
    """Service for handling Razorpay payment processing and subscription management."""
    
    def __init__(self):
        """Initialize Razorpay client with API credentials."""
        settings = get_settings()
        
        if not settings.external.razorpay_key_id or not settings.external.razorpay_key_secret:
            logger.warning("Razorpay credentials not configured")
            self.client = None
            self.webhook_secret = None
            return
            
        self.client = razorpay.Client(
            auth=(
                settings.external.razorpay_key_id,
                settings.external.razorpay_key_secret
            )
        )
        self.webhook_secret = settings.external.razorpay_webhook_secret
        self.settings = settings
        
    def is_configured(self) -> bool:
        """Check if Razorpay is properly configured."""
        return self.client is not None
    
    async def create_subscription_plan(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """Create a subscription plan in Razorpay for a given tier."""
        if not self.is_configured():
            raise ValueError("Razorpay not configured")
            
        tier_config = self.settings.subscription_tiers.get(tier.value)
        if not tier_config:
            raise ValueError(f"Invalid subscription tier: {tier.value}")
            
        # Skip creating plan for free tier
        if tier == SubscriptionTier.FREE:
            return {"id": "free", "amount": 0}
            
        plan_data = {
            "period": "monthly",
            "interval": 1,
            "item": {
                "name": f"ZERO-COMP {tier.value.title()} Plan",
                "description": f"Solar weather API access - {tier.value.title()} tier",
                "amount": tier_config["price"] * 100,  # Convert to paise
                "currency": "INR"
            }
        }
        
        try:
            plan = self.client.plan.create(plan_data)
            logger.info("Created Razorpay plan", plan_id=plan["id"], tier=tier.value)
            return plan
        except Exception as e:
            logger.error("Failed to create Razorpay plan", error=str(e), tier=tier.value)
            raise
    
    async def create_subscription(
        self, 
        user_id: str, 
        tier: SubscriptionTier,
        customer_email: str,
        customer_name: str
    ) -> Dict[str, Any]:
        """Create a subscription for a user."""
        if not self.is_configured():
            raise ValueError("Razorpay not configured")
            
        if tier == SubscriptionTier.FREE:
            return {
                "id": f"free_{user_id}",
                "status": "active",
                "current_start": datetime.utcnow().isoformat(),
                "current_end": (datetime.utcnow() + timedelta(days=365)).isoformat()
            }
            
        tier_config = self.settings.subscription_tiers.get(tier.value)
        if not tier_config:
            raise ValueError(f"Invalid subscription tier: {tier.value}")
            
        # Create customer first
        customer_data = {
            "name": customer_name,
            "email": customer_email,
            "contact": "",
            "notes": {
                "user_id": user_id,
                "tier": tier.value
            }
        }
        
        try:
            customer = self.client.customer.create(customer_data)
            
            # Create subscription
            subscription_data = {
                "plan_id": f"plan_{tier.value}",  # Assume plans are pre-created
                "customer_notify": 1,
                "quantity": 1,
                "total_count": 12,  # 12 months
                "customer_id": customer["id"],
                "notes": {
                    "user_id": user_id,
                    "tier": tier.value
                }
            }
            
            subscription = self.client.subscription.create(subscription_data)
            logger.info(
                "Created Razorpay subscription", 
                subscription_id=subscription["id"],
                user_id=user_id,
                tier=tier.value
            )
            return subscription
            
        except Exception as e:
            logger.error(
                "Failed to create Razorpay subscription", 
                error=str(e), 
                user_id=user_id,
                tier=tier.value
            )
            raise
    
    async def create_payment_link(
        self, 
        tier: SubscriptionTier,
        user_id: str,
        customer_email: str,
        customer_name: str
    ) -> Dict[str, Any]:
        """Create a payment link for subscription upgrade."""
        if not self.is_configured():
            raise ValueError("Razorpay not configured")
            
        if tier == SubscriptionTier.FREE:
            raise ValueError("Cannot create payment link for free tier")
            
        tier_config = self.settings.subscription_tiers.get(tier.value)
        if not tier_config:
            raise ValueError(f"Invalid subscription tier: {tier.value}")
            
        payment_link_data = {
            "amount": tier_config["price"] * 100,  # Convert to paise
            "currency": "INR",
            "accept_partial": False,
            "description": f"ZERO-COMP {tier.value.title()} Plan Subscription",
            "customer": {
                "name": customer_name,
                "email": customer_email
            },
            "notify": {
                "sms": False,
                "email": True
            },
            "reminder_enable": True,
            "notes": {
                "user_id": user_id,
                "tier": tier.value,
                "type": "subscription"
            },
            "callback_url": f"{self.settings.api.cors_origins[0]}/dashboard?payment=success",
            "callback_method": "get"
        }
        
        try:
            payment_link = self.client.payment_link.create(payment_link_data)
            logger.info(
                "Created payment link", 
                link_id=payment_link["id"],
                user_id=user_id,
                tier=tier.value
            )
            return payment_link
            
        except Exception as e:
            logger.error(
                "Failed to create payment link", 
                error=str(e), 
                user_id=user_id,
                tier=tier.value
            )
            raise
    
    async def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature."""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return False
            
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error("Failed to verify webhook signature", error=str(e))
            return False
    
    async def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Razorpay webhook events."""
        event_type = event_data.get("event")
        payload = event_data.get("payload", {})
        
        logger.info("Processing Razorpay webhook", event_type=event_type)
        
        result = {
            "event_type": event_type,
            "processed": False,
            "user_id": None,
            "action": None
        }
        
        try:
            if event_type == "subscription.activated":
                result.update(await self._handle_subscription_activated(payload))
            elif event_type == "subscription.cancelled":
                result.update(await self._handle_subscription_cancelled(payload))
            elif event_type == "subscription.charged":
                result.update(await self._handle_subscription_charged(payload))
            elif event_type == "payment.captured":
                result.update(await self._handle_payment_captured(payload))
            elif event_type == "payment.failed":
                result.update(await self._handle_payment_failed(payload))
            else:
                logger.info("Unhandled webhook event type", event_type=event_type)
                
        except Exception as e:
            logger.error("Error processing webhook event", error=str(e), event_type=event_type)
            
        return result
    
    async def _handle_subscription_activated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription activation webhook."""
        subscription = payload.get("subscription", {})
        notes = subscription.get("notes", {})
        user_id = notes.get("user_id")
        tier = notes.get("tier")
        
        return {
            "processed": True,
            "user_id": user_id,
            "action": "activate_subscription",
            "tier": tier,
            "subscription_id": subscription.get("id"),
            "status": SubscriptionStatus.ACTIVE
        }
    
    async def _handle_subscription_cancelled(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation webhook."""
        subscription = payload.get("subscription", {})
        notes = subscription.get("notes", {})
        user_id = notes.get("user_id")
        
        return {
            "processed": True,
            "user_id": user_id,
            "action": "cancel_subscription",
            "subscription_id": subscription.get("id"),
            "status": SubscriptionStatus.CANCELLED
        }
    
    async def _handle_subscription_charged(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful subscription charge webhook."""
        payment = payload.get("payment", {})
        subscription = payload.get("subscription", {})
        notes = subscription.get("notes", {})
        user_id = notes.get("user_id")
        
        return {
            "processed": True,
            "user_id": user_id,
            "action": "renew_subscription",
            "payment_id": payment.get("id"),
            "subscription_id": subscription.get("id"),
            "amount": payment.get("amount", 0) / 100,  # Convert from paise
            "status": PaymentStatus.CAPTURED
        }
    
    async def _handle_payment_captured(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment capture webhook."""
        payment = payload.get("payment", {})
        notes = payment.get("notes", {})
        user_id = notes.get("user_id")
        tier = notes.get("tier")
        
        return {
            "processed": True,
            "user_id": user_id,
            "action": "payment_captured",
            "payment_id": payment.get("id"),
            "tier": tier,
            "amount": payment.get("amount", 0) / 100,  # Convert from paise
            "status": PaymentStatus.CAPTURED
        }
    
    async def _handle_payment_failed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failure webhook."""
        payment = payload.get("payment", {})
        notes = payment.get("notes", {})
        user_id = notes.get("user_id")
        
        return {
            "processed": True,
            "user_id": user_id,
            "action": "payment_failed",
            "payment_id": payment.get("id"),
            "status": PaymentStatus.FAILED,
            "error_description": payment.get("error_description")
        }
    
    async def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details from Razorpay."""
        if not self.is_configured():
            raise ValueError("Razorpay not configured")
            
        try:
            subscription = self.client.subscription.fetch(subscription_id)
            return subscription
        except Exception as e:
            logger.error("Failed to fetch subscription", error=str(e), subscription_id=subscription_id)
            raise
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription in Razorpay."""
        if not self.is_configured():
            raise ValueError("Razorpay not configured")
            
        try:
            result = self.client.subscription.cancel(subscription_id, {"cancel_at_cycle_end": 0})
            logger.info("Cancelled subscription", subscription_id=subscription_id)
            return result
        except Exception as e:
            logger.error("Failed to cancel subscription", error=str(e), subscription_id=subscription_id)
            raise


# Global service instance
razorpay_service = RazorpayService()


def get_razorpay_service() -> RazorpayService:
    """Get Razorpay service instance."""
    return razorpay_service