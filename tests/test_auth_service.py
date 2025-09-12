"""Unit tests for authentication service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import hashlib

from app.services.auth_service import AuthService, SignUpRequest, SignInRequest, AuthResponse, UserSession


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        with patch('app.services.auth_service.get_supabase_client'), \
             patch('app.services.auth_service.get_supabase_service_client'), \
             patch('app.services.auth_service.get_settings'):
            return AuthService()
    
    @pytest.fixture
    def mock_user_response(self):
        """Mock user response from Supabase."""
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        return mock_user
    
    @pytest.fixture
    def mock_session_response(self):
        """Mock session response from Supabase."""
        mock_session = Mock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"
        mock_session.expires_at = 1704067200  # 2024-01-01 00:00:00 UTC timestamp
        return mock_session
    
    @pytest.mark.asyncio
    async def test_sign_up_success(self, auth_service, mock_user_response, mock_session_response):
        """Test successful user sign up."""
        # Arrange
        request = SignUpRequest(
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        mock_auth_response = Mock()
        mock_auth_response.user = mock_user_response
        mock_auth_response.session = mock_session_response
        
        auth_service.client.auth.sign_up = Mock(return_value=mock_auth_response)
        auth_service._create_user_subscription = AsyncMock()
        
        # Act
        result = await auth_service.sign_up(request)
        
        # Assert
        assert result.success is True
        assert result.user_id == "test-user-id"
        assert result.email == "test@example.com"
        assert result.access_token == "test-access-token"
        assert result.refresh_token == "test-refresh-token"
        
        auth_service.client.auth.sign_up.assert_called_once()
        auth_service._create_user_subscription.assert_called_once_with(
            user_id="test-user-id",
            email="test@example.com"
        )
    
    @pytest.mark.asyncio
    async def test_sign_up_auth_error(self, auth_service):
        """Test sign up with authentication error."""
        # Arrange
        request = SignUpRequest(
            email="test@example.com",
            password="password123"
        )
        
        auth_service.client.auth.sign_up = Mock(side_effect=Exception("Email already exists"))
        
        # Act
        result = await auth_service.sign_up(request)
        
        # Assert
        assert result.success is False
        assert "Email already exists" in result.error_message
    
    @pytest.mark.asyncio
    async def test_sign_in_success(self, auth_service, mock_user_response, mock_session_response):
        """Test successful user sign in."""
        # Arrange
        request = SignInRequest(
            email="test@example.com",
            password="password123"
        )
        
        mock_auth_response = Mock()
        mock_auth_response.user = mock_user_response
        mock_auth_response.session = mock_session_response
        
        auth_service.client.auth.sign_in_with_password = Mock(return_value=mock_auth_response)
        auth_service._update_last_login = AsyncMock()
        
        # Act
        result = await auth_service.sign_in(request)
        
        # Assert
        assert result.success is True
        assert result.user_id == "test-user-id"
        assert result.email == "test@example.com"
        assert result.access_token == "test-access-token"
        
        auth_service._update_last_login.assert_called_once_with("test-user-id")
    
    @pytest.mark.asyncio
    async def test_sign_in_invalid_credentials(self, auth_service):
        """Test sign in with invalid credentials."""
        # Arrange
        request = SignInRequest(
            email="test@example.com",
            password="wrongpassword"
        )
        
        auth_service.client.auth.sign_in_with_password = Mock(
            side_effect=Exception("Invalid login credentials")
        )
        
        # Act
        result = await auth_service.sign_in(request)
        
        # Assert
        assert result.success is False
        assert "Invalid email or password" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, auth_service, mock_user_response):
        """Test successful token validation."""
        # Arrange
        access_token = "valid-access-token"
        
        mock_user_response_obj = Mock()
        mock_user_response_obj.user = mock_user_response
        
        auth_service.client.auth.get_user = Mock(return_value=mock_user_response_obj)
        auth_service._get_user_subscription = AsyncMock(return_value={
            "tier": "pro",
            "api_key": "test-api-key",
            "last_login": None
        })
        
        # Act
        result = await auth_service.validate_token(access_token)
        
        # Assert
        assert result is not None
        assert result.user_id == "test-user-id"
        assert result.email == "test@example.com"
        assert result.subscription_tier == "pro"
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, auth_service):
        """Test token validation with invalid token."""
        # Arrange
        access_token = "invalid-access-token"
        
        auth_service.client.auth.get_user = Mock(side_effect=Exception("Invalid token"))
        
        # Act
        result = await auth_service.validate_token(access_token)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_user_response, mock_session_response):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "valid-refresh-token"
        
        mock_auth_response = Mock()
        mock_auth_response.user = mock_user_response
        mock_auth_response.session = mock_session_response
        
        auth_service.client.auth.refresh_session = Mock(return_value=mock_auth_response)
        
        # Act
        result = await auth_service.refresh_token(refresh_token)
        
        # Assert
        assert result.success is True
        assert result.access_token == "test-access-token"
        assert result.refresh_token == "test-refresh-token"
    
    @pytest.mark.asyncio
    async def test_generate_api_key_success(self, auth_service):
        """Test successful API key generation."""
        # Arrange
        user_id = "test-user-id"
        
        mock_result = Mock()
        mock_result.data = [{"id": "subscription-id"}]
        
        mock_table = Mock()
        mock_table.update.return_value.eq.return_value.execute.return_value = mock_result
        auth_service.service_client.table = Mock(return_value=mock_table)
        
        # Act
        result = await auth_service.generate_api_key(user_id)
        
        # Assert
        assert result is not None
        assert result.startswith("zc_")
        assert len(result) > 10
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, auth_service):
        """Test successful API key validation."""
        # Arrange
        api_key = "zc_test_api_key"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        mock_subscription_result = Mock()
        mock_subscription_result.data = [{
            "user_id": "test-user-id",
            "tier": "pro",
            "webhook_url": None,
            "alert_thresholds": {},
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        mock_user_result = Mock()
        mock_user_result.user = Mock()
        mock_user_result.user.email = "test@example.com"
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_subscription_result
        auth_service.service_client.table = Mock(return_value=mock_table)
        auth_service.service_client.auth.admin.get_user_by_id = Mock(return_value=mock_user_result)
        
        # Act
        result = await auth_service.validate_api_key(api_key)
        
        # Assert
        assert result is not None
        assert result.user_id == "test-user-id"
        assert result.email == "test@example.com"
        assert result.subscription_tier == "pro"
        assert result.api_key == api_key
    
    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, auth_service):
        """Test API key validation with invalid key."""
        # Arrange
        api_key = "invalid_api_key"
        
        mock_result = Mock()
        mock_result.data = []
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
        auth_service.service_client.table = Mock(return_value=mock_table)
        
        # Act
        result = await auth_service.validate_api_key(api_key)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_sign_out_success(self, auth_service):
        """Test successful sign out."""
        # Arrange
        access_token = "test-access-token"
        auth_service.client.auth.sign_out = Mock()
        
        # Act
        result = await auth_service.sign_out(access_token)
        
        # Assert
        assert result is True
        auth_service.client.auth.sign_out.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_subscription(self, auth_service):
        """Test user subscription creation."""
        # Arrange
        user_id = "test-user-id"
        email = "test@example.com"
        
        mock_result = Mock()
        mock_result.data = [{"id": "subscription-id"}]
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = mock_result
        auth_service.service_client.table = Mock(return_value=mock_table)
        
        # Act
        await auth_service._create_user_subscription(user_id, email)
        
        # Assert
        auth_service.service_client.table.assert_called_with("user_subscriptions")
        mock_table.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_subscription(self, auth_service):
        """Test getting user subscription details."""
        # Arrange
        user_id = "test-user-id"
        
        mock_result = Mock()
        mock_result.data = [{
            "tier": "pro",
            "api_key_hash": "hash123",
            "webhook_url": None,
            "alert_thresholds": {},
            "last_login": None
        }]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_result
        auth_service.service_client.table = Mock(return_value=mock_table)
        
        # Act
        result = await auth_service._get_user_subscription(user_id)
        
        # Assert
        assert result["tier"] == "pro"
        assert result["api_key_hash"] == "hash123"