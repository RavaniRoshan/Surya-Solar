"""
API Dependencies for FastAPI
Rate limiting, authentication, and common dependencies
"""

import structlog
from fastapi import HTTPException, Depends, Request
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.auth import get_current_user, get_current_user_optional, TokenData
from app.services.cache import get_cache_service, CacheService
from app.core.metrics import get_metrics_collector, track_api_request

logger = structlog.get_logger()

# Rate limit tiers
TIER_LIMITS = {
    "free": {"daily": 100, "per_minute": 10},
    "pro": {"daily": 10000, "per_minute": 100},
    "enterprise": {"daily": 1000000, "per_minute": 1000}
}


class RateLimitInfo:
    """Rate limit status for current request"""
    def __init__(self, remaining: int, limit: int, reset_at: str, tier: str):
        self.remaining = remaining
        self.limit = limit
        self.reset_at = reset_at
        self.tier = tier


async def get_cache() -> CacheService:
    """Get cache service dependency"""
    cache = get_cache_service()
    await cache.connect()
    return cache


async def check_rate_limit(
    user: TokenData = Depends(get_current_user),
    cache: CacheService = Depends(get_cache)
) -> RateLimitInfo:
    """
    Check and enforce rate limits based on user tier
    
    Raises:
        HTTPException 429 if rate limit exceeded
    
    Returns:
        RateLimitInfo with remaining calls and limit details
    """
    tier = user.tier or "free"
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    
    # Check daily limit
    daily_count = await cache.increment_rate_limit(user.user_id, window="day")
    daily_limit = limits["daily"]
    
    if daily_count > daily_limit:
        logger.warning("rate_limit_exceeded", user_id=user.user_id, tier=tier, type="daily")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Daily limit of {daily_limit} requests exceeded. Upgrade your plan for higher limits.",
                "limit": daily_limit,
                "tier": tier,
                "upgrade_url": "/pricing"
            },
            headers={"Retry-After": "86400", "X-RateLimit-Limit": str(daily_limit), "X-RateLimit-Remaining": "0"}
        )
    
    # Check per-minute limit
    minute_count = await cache.increment_rate_limit(user.user_id, window="minute")
    minute_limit = limits["per_minute"]
    
    if minute_count > minute_limit:
        logger.warning("rate_limit_exceeded", user_id=user.user_id, tier=tier, type="minute")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Per-minute limit of {minute_limit} requests exceeded. Please slow down.",
                "limit": minute_limit,
                "tier": tier
            },
            headers={"Retry-After": "60", "X-RateLimit-Limit": str(minute_limit), "X-RateLimit-Remaining": "0"}
        )
    
    remaining = daily_limit - daily_count
    
    # Calculate reset time (midnight UTC)
    now = datetime.utcnow()
    reset_at = datetime(now.year, now.month, now.day, 23, 59, 59).isoformat() + "Z"
    
    return RateLimitInfo(
        remaining=remaining,
        limit=daily_limit,
        reset_at=reset_at,
        tier=tier
    )


async def optional_rate_limit(
    user: Optional[TokenData] = Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache)
) -> Optional[RateLimitInfo]:
    """
    Optional rate limiting for public endpoints
    Uses IP-based limiting for anonymous users
    """
    if user is None:
        # Anonymous users get very limited access
        return RateLimitInfo(remaining=10, limit=10, reset_at="", tier="anonymous")
    
    return await check_rate_limit(user, cache)


def require_tier(required_tier: str):
    """
    Dependency factory for tier-gated endpoints
    
    Usage:
        @app.get("/enterprise-only")
        async def enterprise_endpoint(user = Depends(require_tier("enterprise"))):
            ...
    """
    tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
    
    async def tier_dependency(user: TokenData = Depends(get_current_user)) -> TokenData:
        user_tier = user.tier or "free"
        
        if tier_hierarchy.get(user_tier, 0) < tier_hierarchy.get(required_tier, 0):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Subscription required",
                    "message": f"This feature requires {required_tier} subscription",
                    "current_tier": user_tier,
                    "required_tier": required_tier,
                    "upgrade_url": "/pricing"
                }
            )
        
        return user
    
    return tier_dependency


class RequestTimer:
    """Context manager for timing API requests"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
            status_code = 500 if exc_type else 200
            track_api_request(self.endpoint, status_code, duration_ms)


async def add_rate_limit_headers(response, rate_limit_info: RateLimitInfo):
    """Add rate limit headers to response"""
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info.limit)
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info.remaining)
    response.headers["X-RateLimit-Reset"] = rate_limit_info.reset_at
    response.headers["X-RateLimit-Tier"] = rate_limit_info.tier
    return response
