"""Session management utilities for user authentication and authorization."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

from app.services.auth_service import AuthService, UserSession, get_auth_service
from app.config import get_settings

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class SessionManager:
    """Manages user sessions and authentication middleware."""
    
    def __init__(self):
        self.auth_service = get_auth_service()
        self.settings = get_settings()
    
    async def get_current_user(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
    ) -> UserSession:
        """
        Get current authenticated user from JWT token.
        
        Args:
            credentials: HTTP Bearer token credentials
            
        Returns:
            UserSession for authenticated user
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_session = await self.auth_service.validate_token(credentials.credentials)
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user_session
    
    async def get_current_user_optional(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
    ) -> Optional[UserSession]:
        """
        Get current authenticated user from JWT token (optional).
        
        Args:
            credentials: HTTP Bearer token credentials
            
        Returns:
            UserSession if authenticated, None otherwise
        """
        if not credentials:
            return None
        
        return await self.auth_service.validate_token(credentials.credentials)
    
    async def get_api_user(
        self, 
        api_key: Optional[str] = Depends(api_key_header)
    ) -> UserSession:
        """
        Get authenticated user from API key.
        
        Args:
            api_key: API key from X-API-Key header
            
        Returns:
            UserSession for API key owner
            
        Raises:
            HTTPException: If API key is invalid
        """
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        user_session = await self.auth_service.validate_api_key(api_key)
        
        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        return user_session
    
    async def get_user_any_auth(
        self,
        bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        api_key: Optional[str] = Depends(api_key_header)
    ) -> UserSession:
        """
        Get authenticated user from either JWT token or API key.
        
        Args:
            bearer_credentials: HTTP Bearer token credentials
            api_key: API key from X-API-Key header
            
        Returns:
            UserSession for authenticated user
            
        Raises:
            HTTPException: If both authentication methods fail
        """
        # Try JWT token first
        if bearer_credentials:
            user_session = await self.auth_service.validate_token(bearer_credentials.credentials)
            if user_session:
                return user_session
        
        # Try API key
        if api_key:
            user_session = await self.auth_service.validate_api_key(api_key)
            if user_session:
                return user_session
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (JWT token or API key)",
            headers={"WWW-Authenticate": "Bearer, ApiKey"}
        )
    
    def require_subscription_tier(self, required_tier: str):
        """
        Dependency factory for requiring specific subscription tier.
        
        Args:
            required_tier: Required subscription tier (free, pro, enterprise)
            
        Returns:
            Dependency function that validates subscription tier
        """
        tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
        required_level = tier_hierarchy.get(required_tier, 0)
        
        async def check_subscription_tier(user: UserSession = Depends(self.get_user_any_auth)) -> UserSession:
            user_level = tier_hierarchy.get(user.subscription_tier, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Subscription tier '{required_tier}' or higher required"
                )
            
            return user
        
        return check_subscription_tier
    
    def require_feature_access(self, feature: str):
        """
        Dependency factory for requiring specific feature access.
        
        Args:
            feature: Required feature (dashboard, api, websocket, csv_export, sla)
            
        Returns:
            Dependency function that validates feature access
        """
        async def check_feature_access(user: UserSession = Depends(self.get_user_any_auth)) -> UserSession:
            tier_features = self.settings.subscription_tiers.get(user.subscription_tier, {}).get("features", [])
            
            if feature not in tier_features:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature}' not available in {user.subscription_tier} tier"
                )
            
            return user
        
        return check_feature_access
    
    async def validate_rate_limit(self, user: UserSession, endpoint: str) -> bool:
        """
        Validate rate limit for user and endpoint.
        
        Args:
            user: User session
            endpoint: API endpoint name
            
        Returns:
            True if within rate limit, False otherwise
        """
        try:
            # Get rate limits for user's subscription tier
            tier_config = self.settings.subscription_tiers.get(user.subscription_tier, {})
            rate_limits = tier_config.get("rate_limits", {})
            
            # For now, return True (rate limiting implementation would go here)
            # This would typically involve checking Redis or database for request counts
            return True
            
        except Exception as e:
            logger.error(f"Rate limit validation error: {e}")
            return False
    
    async def log_api_usage(self, user: UserSession, endpoint: str, response_time_ms: int, status_code: int) -> None:
        """
        Log API usage for analytics and billing.
        
        Args:
            user: User session
            endpoint: API endpoint called
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
        """
        try:
            # This would typically log to database or analytics service
            logger.info(
                f"API usage - User: {user.user_id}, Endpoint: {endpoint}, "
                f"Response time: {response_time_ms}ms, Status: {status_code}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")


# Global session manager instance
session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return session_manager


# Convenience dependency functions
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> UserSession:
    """Get current authenticated user (JWT only)."""
    return await session_manager.get_current_user(credentials)


async def get_api_user(
    api_key: Optional[str] = Depends(api_key_header)
) -> UserSession:
    """Get authenticated user (API key only)."""
    return await session_manager.get_api_user(api_key)


async def get_user_any_auth(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header)
) -> UserSession:
    """Get authenticated user (JWT or API key)."""
    return await session_manager.get_user_any_auth(bearer_credentials, api_key)


def require_pro_tier():
    """Require Pro subscription tier or higher."""
    return session_manager.require_subscription_tier("pro")


def require_enterprise_tier():
    """Require Enterprise subscription tier."""
    return session_manager.require_subscription_tier("enterprise")


def require_api_access():
    """Require API feature access."""
    return session_manager.require_feature_access("api")


def require_websocket_access():
    """Require WebSocket feature access."""
    return session_manager.require_feature_access("websocket")