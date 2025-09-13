"""Subscription tier enforcement middleware."""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, List
import time
import structlog
from datetime import datetime, timedelta

from app.models.core import SubscriptionTier, UserSubscription
from app.repositories.subscriptions import get_subscriptions_repository
from app.services.auth_service import get_auth_service, get_current_user
from app.config import get_settings

logger = structlog.get_logger(__name__)
security = HTTPBearer(auto_error=False)


class SubscriptionEnforcer:
    """Handles subscription tier enforcement and rate limiting."""
    
    def __init__(self):
        self.settings = get_settings()
        self.rate_limit_cache: Dict[str, Dict[str, Any]] = {}
        
    def get_tier_config(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get configuration for a subscription tier."""
        return self.settings.subscription_tiers.get(tier.value, {})
    
    def is_feature_allowed(self, tier: SubscriptionTier, feature: str) -> bool:
        """Check if a feature is allowed for the given tier."""
        tier_config = self.get_tier_config(tier)
        allowed_features = tier_config.get("features", [])
        return feature in allowed_features
    
    def get_rate_limit(self, tier: SubscriptionTier, endpoint_type: str) -> int:
        """Get rate limit for tier and endpoint type."""
        tier_config = self.get_tier_config(tier)
        rate_limits = tier_config.get("rate_limits", {})
        return rate_limits.get(endpoint_type, 0)
    
    def check_rate_limit(
        self, 
        user_id: str, 
        tier: SubscriptionTier, 
        endpoint_type: str,
        window_seconds: int = 3600  # 1 hour window
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if user has exceeded rate limit for endpoint type.
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        rate_limit = self.get_rate_limit(tier, endpoint_type)
        
        # No rate limit means unlimited
        if rate_limit == 0:
            return True, {"limit": "unlimited", "remaining": "unlimited"}
        
        # Get current time window
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Initialize user cache if not exists
        cache_key = f"{user_id}:{endpoint_type}"
        if cache_key not in self.rate_limit_cache:
            self.rate_limit_cache[cache_key] = {
                "requests": [],
                "window_start": window_start
            }
        
        user_cache = self.rate_limit_cache[cache_key]
        
        # Clean old requests outside the window
        user_cache["requests"] = [
            req_time for req_time in user_cache["requests"] 
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        current_requests = len(user_cache["requests"])
        is_allowed = current_requests < rate_limit
        
        if is_allowed:
            # Add current request to cache
            user_cache["requests"].append(current_time)
        
        rate_limit_info = {
            "limit": rate_limit,
            "remaining": max(0, rate_limit - current_requests - (1 if is_allowed else 0)),
            "reset_time": window_start + window_seconds,
            "window_seconds": window_seconds
        }
        
        return is_allowed, rate_limit_info
    
    async def get_user_subscription(
        self, 
        user_id: str,
        subscription_repo = None
    ) -> Optional[UserSubscription]:
        """Get user subscription with caching."""
        if not subscription_repo:
            subscription_repo = get_subscriptions_repository()
        
        try:
            subscription = await subscription_repo.get_by_user_id(user_id)
            
            # Check if subscription is expired
            if subscription and subscription.subscription_end_date:
                if subscription.subscription_end_date < datetime.utcnow():
                    # Downgrade to free tier if expired
                    await subscription_repo.update_subscription_tier(
                        user_id, 
                        SubscriptionTier.FREE
                    )
                    subscription.tier = SubscriptionTier.FREE
                    subscription.is_active = True
            
            return subscription
            
        except Exception as e:
            logger.error("Failed to get user subscription", error=str(e), user_id=user_id)
            return None


# Global enforcer instance
subscription_enforcer = SubscriptionEnforcer()


async def get_subscription_enforcer() -> SubscriptionEnforcer:
    """Get subscription enforcer instance."""
    return subscription_enforcer


async def require_subscription_tier(
    required_tier: SubscriptionTier,
    current_user: dict = Depends(get_current_user),
    enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
) -> UserSubscription:
    """
    Dependency to require a minimum subscription tier.
    
    Args:
        required_tier: Minimum required subscription tier
        current_user: Current authenticated user
        enforcer: Subscription enforcer instance
        
    Returns:
        UserSubscription if user has required tier or higher
        
    Raises:
        HTTPException: If user doesn't have required tier
    """
    subscription = await enforcer.get_user_subscription(current_user["id"])
    
    if not subscription:
        raise HTTPException(
            status_code=403,
            detail="No subscription found. Please subscribe to access this feature."
        )
    
    # Define tier hierarchy
    tier_hierarchy = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.PRO: 1,
        SubscriptionTier.ENTERPRISE: 2
    }
    
    user_tier_level = tier_hierarchy.get(subscription.tier, 0)
    required_tier_level = tier_hierarchy.get(required_tier, 0)
    
    if user_tier_level < required_tier_level:
        raise HTTPException(
            status_code=403,
            detail=f"This feature requires {required_tier.value} tier or higher. "
                   f"Current tier: {subscription.tier.value}"
        )
    
    return subscription


async def require_feature_access(
    feature: str,
    current_user: dict = Depends(get_current_user),
    enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
) -> UserSubscription:
    """
    Dependency to require access to a specific feature.
    
    Args:
        feature: Feature name to check access for
        current_user: Current authenticated user
        enforcer: Subscription enforcer instance
        
    Returns:
        UserSubscription if user has access to feature
        
    Raises:
        HTTPException: If user doesn't have access to feature
    """
    subscription = await enforcer.get_user_subscription(current_user["id"])
    
    if not subscription:
        raise HTTPException(
            status_code=403,
            detail="No subscription found. Please subscribe to access this feature."
        )
    
    if not enforcer.is_feature_allowed(subscription.tier, feature):
        tier_config = enforcer.get_tier_config(subscription.tier)
        allowed_features = tier_config.get("features", [])
        
        raise HTTPException(
            status_code=403,
            detail=f"Feature '{feature}' not available in {subscription.tier.value} tier. "
                   f"Available features: {', '.join(allowed_features)}"
        )
    
    return subscription


async def enforce_rate_limit(
    endpoint_type: str,
    current_user: dict = Depends(get_current_user),
    enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
) -> Dict[str, Any]:
    """
    Dependency to enforce rate limiting based on subscription tier.
    
    Args:
        endpoint_type: Type of endpoint (e.g., 'alerts', 'history', 'websocket')
        current_user: Current authenticated user
        enforcer: Subscription enforcer instance
        
    Returns:
        Rate limit information
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    subscription = await enforcer.get_user_subscription(current_user["id"])
    
    if not subscription:
        # Use free tier limits for users without subscription
        tier = SubscriptionTier.FREE
    else:
        tier = subscription.tier
    
    is_allowed, rate_limit_info = enforcer.check_rate_limit(
        current_user["id"], 
        tier, 
        endpoint_type
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {endpoint_type}. "
                   f"Limit: {rate_limit_info['limit']} requests per hour. "
                   f"Upgrade your subscription for higher limits.",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(int(rate_limit_info["reset_time"])),
                "Retry-After": str(int(rate_limit_info["reset_time"] - time.time()))
            }
        )
    
    return rate_limit_info


async def get_api_key_subscription(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
) -> Optional[UserSubscription]:
    """
    Get subscription from API key authentication.
    
    Args:
        credentials: HTTP authorization credentials
        enforcer: Subscription enforcer instance
        
    Returns:
        UserSubscription if valid API key, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Extract API key from Bearer token
        api_key = credentials.credentials
        
        # Get subscription by API key hash
        subscription_repo = get_subscriptions_repository()
        
        # In a real implementation, you'd hash the API key and compare
        # For now, we'll assume the API key is already hashed
        subscription = await subscription_repo.get_by_api_key_hash(api_key)
        
        if subscription and subscription.is_active:
            # Check if subscription is expired
            if subscription.subscription_end_date:
                if subscription.subscription_end_date < datetime.utcnow():
                    return None
            
            return subscription
        
        return None
        
    except Exception as e:
        logger.error("Failed to validate API key", error=str(e))
        return None


def create_tier_requirement(tier: SubscriptionTier):
    """Create a dependency function for requiring a specific tier."""
    async def tier_dependency(
        current_user: dict = Depends(get_current_user),
        enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
    ) -> UserSubscription:
        return await require_subscription_tier(tier, current_user, enforcer)
    
    return tier_dependency


def create_feature_requirement(feature: str):
    """Create a dependency function for requiring a specific feature."""
    async def feature_dependency(
        current_user: dict = Depends(get_current_user),
        enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
    ) -> UserSubscription:
        return await require_feature_access(feature, current_user, enforcer)
    
    return feature_dependency


def create_rate_limit_enforcement(endpoint_type: str):
    """Create a dependency function for enforcing rate limits."""
    async def rate_limit_dependency(
        current_user: dict = Depends(get_current_user),
        enforcer: SubscriptionEnforcer = Depends(get_subscription_enforcer)
    ) -> Dict[str, Any]:
        return await enforce_rate_limit(endpoint_type, current_user, enforcer)
    
    return rate_limit_dependency


# Pre-defined tier requirements
require_pro_tier = create_tier_requirement(SubscriptionTier.PRO)
require_enterprise_tier = create_tier_requirement(SubscriptionTier.ENTERPRISE)

# Pre-defined feature requirements
require_api_access = create_feature_requirement("api")
require_websocket_access = create_feature_requirement("websocket")
require_csv_export = create_feature_requirement("csv_export")
require_sla = create_feature_requirement("sla")

# Pre-defined rate limit enforcement
enforce_alerts_rate_limit = create_rate_limit_enforcement("alerts")
enforce_history_rate_limit = create_rate_limit_enforcement("history")
enforce_websocket_rate_limit = create_rate_limit_enforcement("websocket")