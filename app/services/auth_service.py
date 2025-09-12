"""Authentication service for user management and session handling."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import secrets
import hashlib
from pydantic import BaseModel, EmailStr

from supabase import Client
from supabase.lib.client_options import ClientOptions
from app.services.supabase_client import get_supabase_client, get_supabase_service_client
from app.config import get_settings

logger = logging.getLogger(__name__)

class AuthResponse(BaseModel):
    """Authentication response model."""
    success: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

class UserSession(BaseModel):
    """User session model."""
    user_id: str
    email: str
    subscription_tier: str = "free"
    api_key: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class SignUpRequest(BaseModel):
    """Sign up request model."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class SignInRequest(BaseModel):
    """Sign in request model."""
    email: EmailStr
    password: str


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.service_client = get_supabase_service_client()
        self.settings = get_settings()
    
    async def sign_up(self, request: SignUpRequest) -> AuthResponse:
        """
        Register a new user with email and password.
        
        Args:
            request: Sign up request with email, password, and optional full name
            
        Returns:
            AuthResponse with success status and user details
        """
        try:
            # Sign up user with Supabase Auth
            auth_response = self.client.auth.sign_up({
                "email": request.email,
                "password": request.password,
                "options": {
                    "data": {
                        "full_name": request.full_name or ""
                    }
                }
            })
            
            if auth_response.user:
                # Create user subscription record with free tier
                await self._create_user_subscription(
                    user_id=auth_response.user.id,
                    email=request.email
                )
                
                logger.info(f"User signed up successfully: {request.email}")
                
                return AuthResponse(
                    success=True,
                    user_id=auth_response.user.id,
                    email=auth_response.user.email,
                    access_token=auth_response.session.access_token if auth_response.session else None,
                    refresh_token=auth_response.session.refresh_token if auth_response.session else None,
                    expires_at=datetime.fromtimestamp(auth_response.session.expires_at) if auth_response.session else None
                )
            else:
                return AuthResponse(
                    success=False,
                    error_message="Failed to create user account"
                )
                
        except Exception as e:
            if "already" in str(e).lower():
                logger.error(f"Authentication error during sign up: {e}")
                return AuthResponse(
                    success=False,
                    error_message=str(e)
                )
            else:
                logger.error(f"Authentication error during sign up: {e}")
                return AuthResponse(
                    success=False,
                    error_message="Authentication failed"
                )
        except Exception as e:
            logger.error(f"Unexpected error during sign up: {e}")
            return AuthResponse(
                success=False,
                error_message="An unexpected error occurred"
            )
    
    async def sign_in(self, request: SignInRequest) -> AuthResponse:
        """
        Sign in user with email and password.
        
        Args:
            request: Sign in request with email and password
            
        Returns:
            AuthResponse with success status and session details
        """
        try:
            # Sign in with Supabase Auth
            auth_response = self.client.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password
            })
            
            if auth_response.user and auth_response.session:
                # Update last login timestamp
                await self._update_last_login(auth_response.user.id)
                
                logger.info(f"User signed in successfully: {request.email}")
                
                return AuthResponse(
                    success=True,
                    user_id=auth_response.user.id,
                    email=auth_response.user.email,
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    expires_at=datetime.fromtimestamp(auth_response.session.expires_at)
                )
            else:
                return AuthResponse(
                    success=False,
                    error_message="Invalid email or password"
                )
                
        except Exception as e:
            if "invalid" in str(e).lower() or "credentials" in str(e).lower():
                logger.error(f"Authentication error during sign in: {e}")
                return AuthResponse(
                    success=False,
                    error_message="Invalid email or password"
                )
            else:
                logger.error(f"Authentication error during sign in: {e}")
                return AuthResponse(
                    success=False,
                    error_message="Authentication failed"
                )
        except Exception as e:
            logger.error(f"Unexpected error during sign in: {e}")
            return AuthResponse(
                success=False,
                error_message="An unexpected error occurred"
            )
    
    async def validate_token(self, access_token: str) -> Optional[UserSession]:
        """
        Validate JWT access token and return user session.
        
        Args:
            access_token: JWT access token to validate
            
        Returns:
            UserSession if token is valid, None otherwise
        """
        try:
            # Get user from token
            user_response = self.client.auth.get_user(access_token)
            
            if user_response.user:
                # Get user subscription details
                subscription = await self._get_user_subscription(user_response.user.id)
                
                return UserSession(
                    user_id=user_response.user.id,
                    email=user_response.user.email,
                    subscription_tier=subscription.get("tier", "free"),
                    api_key=subscription.get("api_key"),
                    is_active=True,
                    created_at=datetime.fromisoformat(user_response.user.created_at.replace('Z', '+00:00')),
                    last_login=subscription.get("last_login")
                )
            
            return None
            
        except Exception as e:
            if "token" in str(e).lower() or "invalid" in str(e).lower():
                logger.warning(f"Token validation failed: {e}")
                return None
            else:
                logger.warning(f"Token validation failed: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token to use for getting new access token
            
        Returns:
            AuthResponse with new tokens or error
        """
        try:
            auth_response = self.client.auth.refresh_session(refresh_token)
            
            if auth_response.session:
                return AuthResponse(
                    success=True,
                    user_id=auth_response.user.id if auth_response.user else None,
                    email=auth_response.user.email if auth_response.user else None,
                    access_token=auth_response.session.access_token,
                    refresh_token=auth_response.session.refresh_token,
                    expires_at=datetime.fromtimestamp(auth_response.session.expires_at)
                )
            else:
                return AuthResponse(
                    success=False,
                    error_message="Failed to refresh token"
                )
                
        except Exception as e:
            if "refresh" in str(e).lower() or "token" in str(e).lower():
                logger.error(f"Token refresh failed: {e}")
                return AuthResponse(
                    success=False,
                    error_message="Invalid refresh token"
                )
            else:
                logger.error(f"Token refresh failed: {e}")
                return AuthResponse(
                    success=False,
                    error_message="Token refresh failed"
                )
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            return AuthResponse(
                success=False,
                error_message="An unexpected error occurred"
            )
    
    async def sign_out(self, access_token: str) -> bool:
        """
        Sign out user and invalidate session.
        
        Args:
            access_token: Access token to invalidate
            
        Returns:
            True if sign out successful, False otherwise
        """
        try:
            self.client.auth.sign_out()
            logger.info("User signed out successfully")
            return True
        except Exception as e:
            logger.error(f"Error during sign out: {e}")
            return False
    
    async def generate_api_key(self, user_id: str) -> Optional[str]:
        """
        Generate a new API key for user.
        
        Args:
            user_id: User ID to generate API key for
            
        Returns:
            Generated API key or None if failed
        """
        try:
            # Generate secure random API key
            api_key = f"zc_{secrets.token_urlsafe(32)}"
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Update user subscription with API key hash
            result = self.service_client.table("user_subscriptions").update({
                "api_key_hash": api_key_hash,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"API key generated for user: {user_id}")
                return api_key
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            return None
    
    async def validate_api_key(self, api_key: str) -> Optional[UserSession]:
        """
        Validate API key and return user session.
        
        Args:
            api_key: API key to validate
            
        Returns:
            UserSession if API key is valid, None otherwise
        """
        try:
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Query user subscription by API key hash
            result = self.service_client.table("user_subscriptions").select(
                "user_id, tier, webhook_url, alert_thresholds, created_at"
            ).eq("api_key_hash", api_key_hash).execute()
            
            if result.data:
                subscription = result.data[0]
                
                # Get user details
                user_result = self.service_client.auth.admin.get_user_by_id(subscription["user_id"])
                
                if user_result.user:
                    return UserSession(
                        user_id=subscription["user_id"],
                        email=user_result.user.email,
                        subscription_tier=subscription["tier"],
                        api_key=api_key,
                        is_active=True,
                        created_at=datetime.fromisoformat(subscription["created_at"])
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    async def _create_user_subscription(self, user_id: str, email: str) -> None:
        """Create initial user subscription with free tier."""
        try:
            self.service_client.table("user_subscriptions").insert({
                "user_id": user_id,
                "tier": "free",
                "alert_thresholds": self.settings.default_alert_thresholds,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Created free tier subscription for user: {email}")
            
        except Exception as e:
            logger.error(f"Failed to create user subscription: {e}")
            raise
    
    async def _get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user subscription details."""
        try:
            result = self.service_client.table("user_subscriptions").select(
                "tier, api_key_hash, webhook_url, alert_thresholds, last_login"
            ).eq("user_id", user_id).execute()
            
            if result.data:
                return result.data[0]
            
            return {"tier": "free"}
            
        except Exception as e:
            logger.error(f"Failed to get user subscription: {e}")
            return {"tier": "free"}
    
    async def _update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        try:
            self.service_client.table("user_subscriptions").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
            
        except Exception as e:
            logger.warning(f"Failed to update last login: {e}")


# Global auth service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the global authentication service instance."""
    return auth_service