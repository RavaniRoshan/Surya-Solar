"""User and subscription management endpoints."""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import secrets
import hashlib
import logging

from app.models.core import (
    UserSubscription,
    SubscriptionTier,
    ErrorResponse
)
from app.services.auth_service import get_auth_service, UserSession, get_current_user
from app.repositories.subscriptions import get_subscriptions_repository
from app.repositories.api_usage import get_api_usage_repository
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])
security = HTTPBearer()
auth_service = get_auth_service()
subscriptions_repo = get_subscriptions_repository()
api_usage_repo = get_api_usage_repository()
settings = get_settings()


# Request/Response Models
class UserProfileResponse(BaseModel):
    """User profile response model."""
    user_id: str
    email: str
    subscription_tier: str
    api_key_exists: bool
    webhook_url: Optional[str] = None
    alert_thresholds: Dict[str, float]
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    """Update user profile request model."""
    webhook_url: Optional[str] = None
    alert_thresholds: Optional[Dict[str, float]] = None


class APIKeyResponse(BaseModel):
    """API key response model."""
    api_key: str
    created_at: datetime
    note: str = "Store this key securely. It will not be shown again."


class SubscriptionUpdateRequest(BaseModel):
    """Subscription update request model."""
    tier: SubscriptionTier
    razorpay_subscription_id: Optional[str] = None


class UsageStatsResponse(BaseModel):
    """User usage statistics response model."""
    current_period: Dict[str, Any]
    rate_limits: Dict[str, int]
    subscription_tier: str
    features_available: list


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="Get User Profile",
    description="Retrieve the current user's profile and subscription information."
)
async def get_user_profile(
    request: Request,
    user_session: UserSession = Depends(get_current_user)
) -> UserProfileResponse:
    """
    Get the current user's profile information.
    
    Returns user details including subscription tier, API key status,
    webhook configuration, and alert thresholds.
    
    **Authentication Required**: Bearer token (JWT or API key)
    """
    try:
        # Get user subscription details
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            # Create default subscription if not exists
            subscription = UserSubscription(
                user_id=user_session.user_id,
                tier=SubscriptionTier.FREE,
                alert_thresholds=settings.default_alert_thresholds
            )
            subscription = await subscriptions_repo.create(subscription)
        
        return UserProfileResponse(
            user_id=user_session.user_id,
            email=user_session.email,
            subscription_tier=subscription.tier.value,
            api_key_exists=subscription.api_key_hash is not None,
            webhook_url=subscription.webhook_url,
            alert_thresholds=subscription.alert_thresholds,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=subscription.subscription_end_date,
            last_login=subscription.last_login,
            created_at=subscription.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user profile"
        )


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update User Profile",
    description="Update user profile settings including webhook URL and alert thresholds."
)
async def update_user_profile(
    request: UpdateProfileRequest,
    user_session: UserSession = Depends(get_current_user)
) -> UserProfileResponse:
    """
    Update the current user's profile settings.
    
    **Updatable Fields**:
    - `webhook_url`: URL for webhook notifications (Pro/Enterprise only)
    - `alert_thresholds`: Custom alert probability thresholds
    
    **Authentication Required**: Bearer token (JWT or API key)
    """
    try:
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="User subscription not found"
            )
        
        # Validate webhook URL for subscription tier
        if request.webhook_url is not None:
            if subscription.tier == SubscriptionTier.FREE:
                raise HTTPException(
                    status_code=403,
                    detail="Webhook URLs require Pro or Enterprise subscription"
                )
        
        # Update fields
        updates = {}
        if request.webhook_url is not None:
            updates['webhook_url'] = request.webhook_url
        
        if request.alert_thresholds is not None:
            # Validate thresholds
            for level, threshold in request.alert_thresholds.items():
                if level not in ['low', 'medium', 'high']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid alert level: {level}"
                    )
                if not 0.0 <= threshold <= 1.0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Alert threshold must be between 0.0 and 1.0: {threshold}"
                    )
            updates['alert_thresholds'] = request.alert_thresholds
        
        # Apply updates
        if updates:
            subscription = await subscriptions_repo.update(subscription.id, updates)
        
        return UserProfileResponse(
            user_id=user_session.user_id,
            email=user_session.email,
            subscription_tier=subscription.tier.value,
            api_key_exists=subscription.api_key_hash is not None,
            webhook_url=subscription.webhook_url,
            alert_thresholds=subscription.alert_thresholds,
            subscription_start_date=subscription.subscription_start_date,
            subscription_end_date=subscription.subscription_end_date,
            last_login=subscription.last_login,
            created_at=subscription.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )


@router.post(
    "/api-key",
    response_model=APIKeyResponse,
    summary="Generate API Key",
    description="Generate a new API key for programmatic access."
)
async def generate_api_key(
    user_session: UserSession = Depends(get_current_user)
) -> APIKeyResponse:
    """
    Generate a new API key for the current user.
    
    **Important**: The API key will only be shown once. Store it securely.
    
    **Subscription Requirements**:
    - Pro tier: Single API key
    - Enterprise tier: Multiple API keys (future feature)
    
    **Authentication Required**: Bearer token (JWT only, not API key)
    """
    try:
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="User subscription not found"
            )
        
        # Check subscription tier
        if subscription.tier == SubscriptionTier.FREE:
            raise HTTPException(
                status_code=403,
                detail="API key generation requires Pro or Enterprise subscription"
            )
        
        # Generate new API key
        api_key = f"zc_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Update subscription with new API key hash
        await subscriptions_repo.update(subscription.id, {
            'api_key_hash': api_key_hash,
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"API key generated for user: {user_session.user_id}")
        
        return APIKeyResponse(
            api_key=api_key,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate API key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate API key"
        )


@router.delete(
    "/api-key",
    summary="Revoke API Key",
    description="Revoke the current user's API key."
)
async def revoke_api_key(
    user_session: UserSession = Depends(get_current_user)
):
    """
    Revoke the current user's API key.
    
    This will immediately invalidate the API key and prevent its use
    for authentication.
    
    **Authentication Required**: Bearer token (JWT only, not API key)
    """
    try:
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="User subscription not found"
            )
        
        if not subscription.api_key_hash:
            raise HTTPException(
                status_code=404,
                detail="No API key found to revoke"
            )
        
        # Remove API key hash
        await subscriptions_repo.update(subscription.id, {
            'api_key_hash': None,
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"API key revoked for user: {user_session.user_id}")
        
        return {"message": "API key revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke API key"
        )


@router.get(
    "/usage",
    response_model=UsageStatsResponse,
    summary="Get Usage Statistics",
    description="Get current usage statistics and rate limit information."
)
async def get_usage_statistics(
    hours_back: int = 24,
    user_session: UserSession = Depends(get_current_user)
) -> UsageStatsResponse:
    """
    Get usage statistics for the current user.
    
    **Parameters**:
    - `hours_back`: Number of hours to analyze (default: 24)
    
    **Returns**:
    - Current period usage statistics
    - Rate limits for subscription tier
    - Available features
    
    **Authentication Required**: Bearer token (JWT or API key)
    """
    try:
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="User subscription not found"
            )
        
        # Get usage statistics
        usage_stats = await api_usage_repo.get_user_statistics(
            user_session.user_id, 
            hours_back
        )
        
        # Get tier configuration
        tier_config = settings.subscription_tiers.get(subscription.tier.value, {})
        rate_limits = tier_config.get("rate_limits", {})
        features = tier_config.get("features", [])
        
        return UsageStatsResponse(
            current_period=usage_stats,
            rate_limits=rate_limits,
            subscription_tier=subscription.tier.value,
            features_available=features
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve usage statistics"
        )


@router.get(
    "/subscription",
    response_model=UserSubscription,
    summary="Get Subscription Details",
    description="Get detailed subscription information."
)
async def get_subscription_details(
    user_session: UserSession = Depends(get_current_user)
) -> UserSubscription:
    """
    Get detailed subscription information for the current user.
    
    **Authentication Required**: Bearer token (JWT or API key)
    """
    try:
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="User subscription not found"
            )
        
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription details: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve subscription details"
        )


@router.put(
    "/subscription",
    response_model=UserSubscription,
    summary="Update Subscription",
    description="Update subscription tier (typically called by payment webhooks)."
)
async def update_subscription(
    request: SubscriptionUpdateRequest,
    user_session: UserSession = Depends(get_current_user)
) -> UserSubscription:
    """
    Update user subscription tier.
    
    **Note**: This endpoint is typically used by payment processing webhooks.
    For user-initiated upgrades, use the payment flow through the dashboard.
    
    **Authentication Required**: Bearer token (JWT or API key)
    """
    try:
        subscription = await subscriptions_repo.get_by_user_id(user_session.user_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="User subscription not found"
            )
        
        # Update subscription tier
        updated_subscription = await subscriptions_repo.update_subscription_tier(
            user_session.user_id,
            request.tier,
            request.razorpay_subscription_id
        )
        
        if not updated_subscription:
            raise HTTPException(
                status_code=500,
                detail="Failed to update subscription"
            )
        
        logger.info(f"Subscription updated for user {user_session.user_id}: {request.tier.value}")
        
        return updated_subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update subscription: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update subscription"
        )