"""Tests for user management API endpoints."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.core import UserSubscription, SubscriptionTier
from app.services.auth_service import UserSession


@pytest.fixture
def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user_session():
    """Mock user session for testing."""
    return UserSession(
        user_id="test-user-123",
        email="test@example.com",
        subscription_tier="pro",
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_subscription():
    """Mock subscription for testing."""
    return UserSubscription(
        id="sub-123",
        user_id="test-user-123",
        tier=SubscriptionTier.PRO,
        api_key_hash="hashed_key",
        webhook_url="https://example.com/webhook",
        alert_thresholds={"low": 0.3, "medium": 0.6, "high": 0.8},
        is_active=True,
        created_at=datetime.utcnow()
    )


class TestUserProfileEndpoints:
    """Test cases for user profile endpoints."""
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_get_user_profile_success(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful user profile retrieval."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        
        response = client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "test@example.com"
        assert data["subscription_tier"] == "pro"
        assert data["api_key_exists"] is True
        assert data["webhook_url"] == "https://example.com/webhook"
        assert "alert_thresholds" in data
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_update_user_profile_success(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful user profile update."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        mock_subscriptions_repo.update = AsyncMock(return_value=mock_subscription)
        
        update_data = {
            "webhook_url": "https://newwebhook.com/alerts",
            "alert_thresholds": {
                "low": 0.2,
                "medium": 0.5,
                "high": 0.9
            }
        }
        
        response = client.put(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer test-token"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test-user-123"
        mock_subscriptions_repo.update.assert_called_once()
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_update_profile_free_tier_webhook_restriction(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test webhook URL restriction for free tier users."""
        free_subscription = UserSubscription(
            id="sub-123",
            user_id="test-user-123",
            tier=SubscriptionTier.FREE,
            is_active=True
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=free_subscription)
        
        update_data = {
            "webhook_url": "https://example.com/webhook"
        }
        
        response = client.put(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer test-token"},
            json=update_data
        )
        
        assert response.status_code == 403
        assert "Pro or Enterprise subscription" in response.json()["detail"]


class TestAPIKeyEndpoints:
    """Test cases for API key management endpoints."""
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_generate_api_key_success(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful API key generation."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        mock_subscriptions_repo.update = AsyncMock(return_value=mock_subscription)
        
        response = client.post(
            "/api/v1/users/api-key",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "api_key" in data
        assert data["api_key"].startswith("zc_")
        assert "created_at" in data
        assert "note" in data
        
        mock_subscriptions_repo.update.assert_called_once()
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_generate_api_key_free_tier_restriction(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test API key generation restriction for free tier."""
        free_subscription = UserSubscription(
            id="sub-123",
            user_id="test-user-123",
            tier=SubscriptionTier.FREE,
            is_active=True
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=free_subscription)
        
        response = client.post(
            "/api/v1/users/api-key",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 403
        assert "Pro or Enterprise subscription" in response.json()["detail"]
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_revoke_api_key_success(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful API key revocation."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        mock_subscriptions_repo.update = AsyncMock(return_value=mock_subscription)
        
        response = client.delete(
            "/api/v1/users/api-key",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "API key revoked successfully"
        mock_subscriptions_repo.update.assert_called_once()
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_revoke_api_key_not_found(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test API key revocation when no key exists."""
        subscription_no_key = UserSubscription(
            id="sub-123",
            user_id="test-user-123",
            tier=SubscriptionTier.PRO,
            api_key_hash=None,  # No API key
            is_active=True
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=subscription_no_key)
        
        response = client.delete(
            "/api/v1/users/api-key",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 404
        assert "No API key found" in response.json()["detail"]


class TestUsageStatisticsEndpoint:
    """Test cases for usage statistics endpoint."""
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    @patch('app.api.users.api_usage_repo')
    def test_get_usage_statistics_success(
        self,
        mock_api_usage_repo,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful usage statistics retrieval."""
        mock_usage_stats = {
            "total_requests": 150,
            "success_count": 145,
            "error_count": 5,
            "avg_response_time": 120.5,
            "hours_analyzed": 24
        }
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        mock_api_usage_repo.get_user_statistics = AsyncMock(return_value=mock_usage_stats)
        
        response = client.get(
            "/api/v1/users/usage",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_period"] == mock_usage_stats
        assert data["subscription_tier"] == "pro"
        assert "rate_limits" in data
        assert "features_available" in data


class TestSubscriptionEndpoints:
    """Test cases for subscription management endpoints."""
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_get_subscription_details_success(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful subscription details retrieval."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        
        response = client.get(
            "/api/v1/users/subscription",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test-user-123"
        assert data["tier"] == "pro"
        assert data["is_active"] is True
    
    @patch('app.api.users.auth_service')
    @patch('app.api.users.subscriptions_repo')
    def test_update_subscription_success(
        self,
        mock_subscriptions_repo,
        mock_auth_service,
        client,
        mock_user_session,
        mock_subscription
    ):
        """Test successful subscription update."""
        updated_subscription = UserSubscription(
            id="sub-123",
            user_id="test-user-123",
            tier=SubscriptionTier.ENTERPRISE,
            is_active=True
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        mock_subscriptions_repo.update_subscription_tier = AsyncMock(return_value=updated_subscription)
        
        update_data = {
            "tier": "enterprise",
            "razorpay_subscription_id": "sub_razorpay_123"
        }
        
        response = client.put(
            "/api/v1/users/subscription",
            headers={"Authorization": "Bearer test-token"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tier"] == "enterprise"
        mock_subscriptions_repo.update_subscription_tier.assert_called_once_with(
            "test-user-123",
            SubscriptionTier.ENTERPRISE,
            "sub_razorpay_123"
        )


class TestAuthenticationAndValidation:
    """Test authentication and input validation."""
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to user endpoints."""
        endpoints = [
            "/api/v1/users/profile",
            "/api/v1/users/usage",
            "/api/v1/users/subscription"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 403  # No auth header
    
    @patch('app.api.users.auth_service')
    def test_invalid_token(self, mock_auth_service, client):
        """Test invalid token handling."""
        mock_auth_service.validate_token = AsyncMock(return_value=None)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        
        response = client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_invalid_alert_thresholds(self, client):
        """Test validation of alert thresholds."""
        with patch('app.api.users.auth_service') as mock_auth_service, \
             patch('app.api.users.subscriptions_repo') as mock_subscriptions_repo:
            
            mock_user = UserSession(
                user_id="test-user",
                email="test@example.com",
                subscription_tier="pro",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            mock_subscription = UserSubscription(
                id="sub-123",
                user_id="test-user",
                tier=SubscriptionTier.PRO,
                is_active=True
            )
            
            mock_auth_service.validate_token = AsyncMock(return_value=mock_user)
            mock_auth_service.validate_api_key = AsyncMock(return_value=None)
            mock_subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
            
            # Test invalid threshold value
            invalid_data = {
                "alert_thresholds": {
                    "low": 1.5,  # Invalid: > 1.0
                    "medium": 0.6,
                    "high": 0.8
                }
            }
            
            response = client.put(
                "/api/v1/users/profile",
                headers={"Authorization": "Bearer test-token"},
                json=invalid_data
            )
            
            assert response.status_code == 400
            assert "between 0.0 and 1.0" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])