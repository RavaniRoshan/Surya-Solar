"""Unit tests for authentication service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from jose import jwt

from app.services.auth_service import (
    AuthService,
    UserSession,
    create_access_token,
    verify_token,
    hash_api_key,
    verify_api_key
)
from app.config import get_settings


class TestUserSession:
    """Test UserSession model."""
    
    def test_user_session_creation(self):
        """Test UserSession creation with valid data."""
        session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="pro",
            api_key="test-api-key",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        assert session.user_id == "test-user-123"
        assert session.email == "test@example.com"
        assert session.subscription_tier == "pro"
        assert session.is_active is True
    
    def test_user_session_defaults(self):
        """Test UserSession with default values."""
        session = UserSession(
            user_id="test-user",
            email="test@example.com"
        )
        
        assert session.subscription_tier == "free"
        assert session.is_active is True
        assert session.api_key is None
        assert session.webhook_url is None


class TestTokenFunctions:
    """Test token creation and verification functions."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"user_id": "test-user", "email": "test@example.com"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        settings = get_settings()
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        assert decoded["user_id"] == "test-user"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded
    
    def test_create_access_token_default_expiry(self):
        """Test token creation with default expiry."""
        data = {"user_id": "test-user"}
        token = create_access_token(data)
        
        settings = get_settings()
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        
        # Should expire in 24 hours by default
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now
        
        assert 23 <= time_diff.total_seconds() / 3600 <= 25  # ~24 hours
    
    def test_verify_token_valid(self):
        """Test verification of valid token."""
        data = {"user_id": "test-user", "email": "test@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload["user_id"] == "test-user"
        assert payload["email"] == "test@example.com"
    
    def test_verify_token_expired(self):
        """Test verification of expired token."""
        data = {"user_id": "test-user"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        payload = verify_token(token)
        assert payload is None
    
    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        payload = verify_token("invalid.token.here")
        assert payload is None
    
    def test_verify_token_malformed(self):
        """Test verification of malformed token."""
        payload = verify_token("not-a-jwt-token")
        assert payload is None


class TestAPIKeyFunctions:
    """Test API key hashing and verification."""
    
    def test_hash_api_key(self):
        """Test API key hashing."""
        api_key = "test-api-key-123"
        hashed = hash_api_key(api_key)
        
        assert isinstance(hashed, str)
        assert hashed != api_key
        assert len(hashed) > 0
    
    def test_verify_api_key_correct(self):
        """Test API key verification with correct key."""
        api_key = "test-api-key-123"
        hashed = hash_api_key(api_key)
        
        assert verify_api_key(api_key, hashed) is True
    
    def test_verify_api_key_incorrect(self):
        """Test API key verification with incorrect key."""
        api_key = "test-api-key-123"
        wrong_key = "wrong-api-key"
        hashed = hash_api_key(api_key)
        
        assert verify_api_key(wrong_key, hashed) is False
    
    def test_verify_api_key_empty(self):
        """Test API key verification with empty values."""
        assert verify_api_key("", "") is False
        assert verify_api_key("key", "") is False
        assert verify_api_key("", "hash") is False


class TestAuthService:
    """Test AuthService class."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing."""
        return AuthService()
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_client.auth = MagicMock()
        mock_client.table = MagicMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_sign_up_success(self, auth_service, mock_supabase_client):
        """Test successful user sign up."""
        mock_response = MagicMock()
        mock_response.user = MagicMock()
        mock_response.user.id = "new-user-123"
        mock_response.user.email = "newuser@example.com"
        
        mock_supabase_client.auth.sign_up.return_value = mock_response
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            result = await auth_service.sign_up("newuser@example.com", "password123")
        
        assert result["user_id"] == "new-user-123"
        assert result["email"] == "newuser@example.com"
        assert "access_token" in result
        
        mock_supabase_client.auth.sign_up.assert_called_once_with({
            "email": "newuser@example.com",
            "password": "password123"
        })
    
    @pytest.mark.asyncio
    async def test_sign_up_failure(self, auth_service, mock_supabase_client):
        """Test sign up failure."""
        mock_supabase_client.auth.sign_up.side_effect = Exception("Email already exists")
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            with pytest.raises(ValueError, match="Failed to create user"):
                await auth_service.sign_up("existing@example.com", "password123")
    
    @pytest.mark.asyncio
    async def test_sign_in_success(self, auth_service, mock_supabase_client):
        """Test successful user sign in."""
        mock_response = MagicMock()
        mock_response.user = MagicMock()
        mock_response.user.id = "user-123"
        mock_response.user.email = "user@example.com"
        mock_response.session = MagicMock()
        mock_response.session.access_token = "supabase-token"
        
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_response
        
        # Mock subscription lookup
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"tier": "pro", "api_key_hash": "hashed-key", "webhook_url": None}
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            result = await auth_service.sign_in("user@example.com", "password123")
        
        assert result["user_id"] == "user-123"
        assert result["email"] == "user@example.com"
        assert result["subscription_tier"] == "pro"
        assert "access_token" in result
    
    @pytest.mark.asyncio
    async def test_sign_in_invalid_credentials(self, auth_service, mock_supabase_client):
        """Test sign in with invalid credentials."""
        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            with pytest.raises(ValueError, match="Invalid email or password"):
                await auth_service.sign_in("user@example.com", "wrongpassword")
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, auth_service, mock_supabase_client):
        """Test successful token validation."""
        # Create a valid token
        token_data = {"user_id": "user-123", "email": "user@example.com"}
        token = create_access_token(token_data)
        
        # Mock subscription lookup
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"tier": "pro", "api_key_hash": "hashed-key", "webhook_url": None}
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            session = await auth_service.validate_token(token)
        
        assert session is not None
        assert session.user_id == "user-123"
        assert session.email == "user@example.com"
        assert session.subscription_tier == "pro"
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, auth_service):
        """Test validation of invalid token."""
        session = await auth_service.validate_token("invalid-token")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_validate_token_user_not_found(self, auth_service, mock_supabase_client):
        """Test token validation when user not found in database."""
        token_data = {"user_id": "nonexistent-user", "email": "user@example.com"}
        token = create_access_token(token_data)
        
        # Mock empty subscription lookup
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=None
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            session = await auth_service.validate_token(token)
        
        # Should still return session with default values
        assert session is not None
        assert session.subscription_tier == "free"
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, auth_service, mock_supabase_client):
        """Test successful API key validation."""
        api_key = "test-api-key-123"
        hashed_key = hash_api_key(api_key)
        
        # Mock API key lookup
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={
                "user_id": "user-123",
                "tier": "pro",
                "api_key_hash": hashed_key,
                "webhook_url": "https://example.com/webhook"
            }
        )
        mock_supabase_client.table.return_value = mock_table
        
        # Mock user lookup
        mock_auth_table = MagicMock()
        mock_auth_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"email": "user@example.com"}
        )
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            # Mock different table calls
            def mock_table_call(table_name):
                if table_name == "user_subscriptions":
                    return mock_table
                elif table_name == "auth.users":
                    return mock_auth_table
                return MagicMock()
            
            mock_supabase_client.table.side_effect = mock_table_call
            
            session = await auth_service.validate_api_key(api_key)
        
        assert session is not None
        assert session.user_id == "user-123"
        assert session.email == "user@example.com"
        assert session.subscription_tier == "pro"
        assert session.webhook_url == "https://example.com/webhook"
    
    @pytest.mark.asyncio
    async def test_validate_api_key_not_found(self, auth_service, mock_supabase_client):
        """Test API key validation when key not found."""
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=None
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            session = await auth_service.validate_api_key("nonexistent-key")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_validate_api_key_wrong_key(self, auth_service, mock_supabase_client):
        """Test API key validation with wrong key."""
        correct_key = "correct-api-key"
        wrong_key = "wrong-api-key"
        hashed_key = hash_api_key(correct_key)
        
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={
                "user_id": "user-123",
                "tier": "pro",
                "api_key_hash": hashed_key
            }
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            session = await auth_service.validate_api_key(wrong_key)
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_generate_api_key(self, auth_service, mock_supabase_client):
        """Test API key generation."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            api_key = await auth_service.generate_api_key("user-123")
        
        assert isinstance(api_key, str)
        assert len(api_key) > 0
        assert api_key.startswith("zc_")  # ZERO-COMP prefix
        
        # Verify database update was called
        mock_table.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self, auth_service, mock_supabase_client):
        """Test API key revocation."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            result = await auth_service.revoke_api_key("user-123")
        
        assert result is True
        
        # Verify database update was called to set api_key_hash to null
        mock_table.update.assert_called_once_with({"api_key_hash": None})
    
    @pytest.mark.asyncio
    async def test_update_webhook_url(self, auth_service, mock_supabase_client):
        """Test webhook URL update."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        webhook_url = "https://example.com/webhook"
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            result = await auth_service.update_webhook_url("user-123", webhook_url)
        
        assert result is True
        
        # Verify database update was called
        mock_table.update.assert_called_once_with({"webhook_url": webhook_url})
    
    @pytest.mark.asyncio
    async def test_get_user_subscription(self, auth_service, mock_supabase_client):
        """Test getting user subscription details."""
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={
                "tier": "enterprise",
                "api_key_hash": "hashed-key",
                "webhook_url": "https://example.com/webhook",
                "alert_thresholds": {"high": 0.8, "medium": 0.6},
                "created_at": "2024-01-01T00:00:00Z"
            }
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            subscription = await auth_service.get_user_subscription("user-123")
        
        assert subscription is not None
        assert subscription["tier"] == "enterprise"
        assert subscription["webhook_url"] == "https://example.com/webhook"
        assert "alert_thresholds" in subscription
    
    @pytest.mark.asyncio
    async def test_get_user_subscription_not_found(self, auth_service, mock_supabase_client):
        """Test getting subscription for user that doesn't exist."""
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=None
        )
        mock_supabase_client.table.return_value = mock_table
        
        with patch.object(auth_service, 'supabase', mock_supabase_client):
            subscription = await auth_service.get_user_subscription("nonexistent-user")
        
        assert subscription is None


class TestErrorHandling:
    """Test error handling in auth service."""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        auth_service = AuthService()
        
        with patch.object(auth_service, 'supabase') as mock_supabase:
            mock_supabase.table.side_effect = Exception("Connection failed")
            
            session = await auth_service.validate_token("any-token")
            assert session is None
    
    @pytest.mark.asyncio
    async def test_malformed_database_response(self):
        """Test handling of malformed database responses."""
        auth_service = AuthService()
        
        with patch.object(auth_service, 'supabase') as mock_supabase:
            mock_table = MagicMock()
            mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"invalid": "structure"}  # Missing required fields
            )
            mock_supabase.table.return_value = mock_table
            
            # Should handle gracefully and return session with defaults
            token_data = {"user_id": "user-123", "email": "user@example.com"}
            token = create_access_token(token_data)
            
            session = await auth_service.validate_token(token)
            assert session is not None
            assert session.subscription_tier == "free"  # Default value


if __name__ == "__main__":
    pytest.main([__file__])