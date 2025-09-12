"""Unit tests for session manager."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.services.session_manager import SessionManager, UserSession
from datetime import datetime


class TestSessionManager:
    """Test cases for SessionManager."""
    
    @pytest.fixture
    def session_manager(self):
        """Create SessionManager instance for testing."""
        with patch('app.services.session_manager.get_auth_service'), \
             patch('app.services.session_manager.get_settings'):
            return SessionManager()
    
    @pytest.fixture
    def mock_user_session(self):
        """Mock user session for testing."""
        return UserSession(
            user_id="test-user-id",
            email="test@example.com",
            subscription_tier="pro",
            api_key="test-api-key",
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, session_manager, mock_user_session):
        """Test successful user authentication with JWT token."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-jwt-token"
        )
        
        session_manager.auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        
        # Act
        result = await session_manager.get_current_user(credentials)
        
        # Assert
        assert result == mock_user_session
        session_manager.auth_service.validate_token.assert_called_once_with("valid-jwt-token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self, session_manager):
        """Test user authentication without credentials."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await session_manager.get_current_user(None)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, session_manager):
        """Test user authentication with invalid JWT token."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-jwt-token"
        )
        
        session_manager.auth_service.validate_token = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await session_manager.get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_success(self, session_manager, mock_user_session):
        """Test optional user authentication with valid token."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-jwt-token"
        )
        
        session_manager.auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        
        # Act
        result = await session_manager.get_current_user_optional(credentials)
        
        # Assert
        assert result == mock_user_session
    
    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self, session_manager):
        """Test optional user authentication without credentials."""
        # Act
        result = await session_manager.get_current_user_optional(None)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_api_user_success(self, session_manager, mock_user_session):
        """Test successful API key authentication."""
        # Arrange
        api_key = "zc_valid_api_key"
        session_manager.auth_service.validate_api_key = AsyncMock(return_value=mock_user_session)
        
        # Act
        result = await session_manager.get_api_user(api_key)
        
        # Assert
        assert result == mock_user_session
        session_manager.auth_service.validate_api_key.assert_called_once_with(api_key)
    
    @pytest.mark.asyncio
    async def test_get_api_user_no_key(self, session_manager):
        """Test API key authentication without key."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await session_manager.get_api_user(None)
        
        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_api_user_invalid_key(self, session_manager):
        """Test API key authentication with invalid key."""
        # Arrange
        api_key = "invalid_api_key"
        session_manager.auth_service.validate_api_key = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await session_manager.get_api_user(api_key)
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_any_auth_jwt_success(self, session_manager, mock_user_session):
        """Test authentication with JWT token (any auth method)."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-jwt-token"
        )
        
        session_manager.auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        
        # Act
        result = await session_manager.get_user_any_auth(credentials, None)
        
        # Assert
        assert result == mock_user_session
    
    @pytest.mark.asyncio
    async def test_get_user_any_auth_api_key_success(self, session_manager, mock_user_session):
        """Test authentication with API key (any auth method)."""
        # Arrange
        api_key = "zc_valid_api_key"
        session_manager.auth_service.validate_token = AsyncMock(return_value=None)
        session_manager.auth_service.validate_api_key = AsyncMock(return_value=mock_user_session)
        
        # Act
        result = await session_manager.get_user_any_auth(None, api_key)
        
        # Assert
        assert result == mock_user_session
    
    @pytest.mark.asyncio
    async def test_get_user_any_auth_no_auth(self, session_manager):
        """Test authentication without any credentials."""
        # Arrange
        session_manager.auth_service.validate_token = AsyncMock(return_value=None)
        session_manager.auth_service.validate_api_key = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await session_manager.get_user_any_auth(None, None)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_subscription_tier_success(self, session_manager):
        """Test subscription tier requirement with sufficient tier."""
        # Arrange
        user = UserSession(
            user_id="test-user-id",
            email="test@example.com",
            subscription_tier="enterprise",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        check_tier = session_manager.require_subscription_tier("pro")
        
        # Mock the dependency
        with patch.object(session_manager, 'get_user_any_auth', return_value=user):
            # Act
            result = await check_tier(user)
            
            # Assert
            assert result == user
    
    @pytest.mark.asyncio
    async def test_require_subscription_tier_insufficient(self, session_manager):
        """Test subscription tier requirement with insufficient tier."""
        # Arrange
        user = UserSession(
            user_id="test-user-id",
            email="test@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        check_tier = session_manager.require_subscription_tier("pro")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_tier(user)
        
        assert exc_info.value.status_code == 403
        assert "Subscription tier 'pro' or higher required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_feature_access_success(self, session_manager):
        """Test feature access requirement with access granted."""
        # Arrange
        user = UserSession(
            user_id="test-user-id",
            email="test@example.com",
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock settings
        session_manager.settings.subscription_tiers = {
            "pro": {
                "features": ["dashboard", "api", "websocket"]
            }
        }
        
        check_feature = session_manager.require_feature_access("api")
        
        # Act
        result = await check_feature(user)
        
        # Assert
        assert result == user
    
    @pytest.mark.asyncio
    async def test_require_feature_access_denied(self, session_manager):
        """Test feature access requirement with access denied."""
        # Arrange
        user = UserSession(
            user_id="test-user-id",
            email="test@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock settings
        session_manager.settings.subscription_tiers = {
            "free": {
                "features": ["dashboard"]
            }
        }
        
        check_feature = session_manager.require_feature_access("api")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await check_feature(user)
        
        assert exc_info.value.status_code == 403
        assert "Feature 'api' not available in free tier" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_rate_limit(self, session_manager, mock_user_session):
        """Test rate limit validation."""
        # Act
        result = await session_manager.validate_rate_limit(mock_user_session, "alerts")
        
        # Assert
        assert result is True  # Currently always returns True
    
    @pytest.mark.asyncio
    async def test_log_api_usage(self, session_manager, mock_user_session):
        """Test API usage logging."""
        # Act (should not raise exception)
        await session_manager.log_api_usage(
            user=mock_user_session,
            endpoint="/api/v1/alerts/current",
            response_time_ms=150,
            status_code=200
        )
        
        # Assert - no exception raised means success