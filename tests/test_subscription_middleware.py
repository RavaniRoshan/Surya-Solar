"""Tests for subscription middleware and tier enforcement."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import time

from fastapi import HTTPException
from app.middleware.subscription import (
    SubscriptionEnforcer,
    require_subscription_tier,
    require_feature_access,
    enforce_rate_limit,
    get_api_key_subscription
)
from app.models.core import SubscriptionTier, UserSubscription


class TestSubscriptionEnforcer:
    """Test cases for SubscriptionEnforcer."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with subscription tiers."""
        with patch('app.middleware.subscription.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.subscription_tiers = {
                "free": {
                    "price": 0,
                    "features": ["dashboard"],
                    "rate_limits": {"alerts": 10, "history": 5}
                },
                "pro": {
                    "price": 50,
                    "features": ["dashboard", "api", "websocket"],
                    "rate_limits": {"alerts": 1000, "history": 500, "websocket": True}
                },
                "enterprise": {
                    "price": 500,
                    "features": ["dashboard", "api", "websocket", "csv_export", "sla"],
                    "rate_limits": {"alerts": 10000, "history": 5000, "websocket": True}
                }
            }
            mock_get_settings.return_value = mock_settings
            yield mock_settings
    
    @pytest.fixture
    def enforcer(self, mock_settings):
        """Create SubscriptionEnforcer instance."""
        return SubscriptionEnforcer()
    
    def test_get_tier_config(self, enforcer):
        """Test getting tier configuration."""
        free_config = enforcer.get_tier_config(SubscriptionTier.FREE)
        assert free_config["price"] == 0
        assert "dashboard" in free_config["features"]
        
        pro_config = enforcer.get_tier_config(SubscriptionTier.PRO)
        assert pro_config["price"] == 50
        assert "api" in pro_config["features"]
        
        enterprise_config = enforcer.get_tier_config(SubscriptionTier.ENTERPRISE)
        assert enterprise_config["price"] == 500
        assert "sla" in enterprise_config["features"]
    
    def test_is_feature_allowed(self, enforcer):
        """Test feature access checking."""
        # Free tier
        assert enforcer.is_feature_allowed(SubscriptionTier.FREE, "dashboard") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.FREE, "api") is False
        assert enforcer.is_feature_allowed(SubscriptionTier.FREE, "websocket") is False
        
        # Pro tier
        assert enforcer.is_feature_allowed(SubscriptionTier.PRO, "dashboard") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.PRO, "api") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.PRO, "websocket") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.PRO, "csv_export") is False
        
        # Enterprise tier
        assert enforcer.is_feature_allowed(SubscriptionTier.ENTERPRISE, "dashboard") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.ENTERPRISE, "api") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.ENTERPRISE, "websocket") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.ENTERPRISE, "csv_export") is True
        assert enforcer.is_feature_allowed(SubscriptionTier.ENTERPRISE, "sla") is True
    
    def test_get_rate_limit(self, enforcer):
        """Test rate limit retrieval."""
        # Free tier
        assert enforcer.get_rate_limit(SubscriptionTier.FREE, "alerts") == 10
        assert enforcer.get_rate_limit(SubscriptionTier.FREE, "history") == 5
        assert enforcer.get_rate_limit(SubscriptionTier.FREE, "websocket") == 0  # Not configured
        
        # Pro tier
        assert enforcer.get_rate_limit(SubscriptionTier.PRO, "alerts") == 1000
        assert enforcer.get_rate_limit(SubscriptionTier.PRO, "history") == 500
        
        # Enterprise tier
        assert enforcer.get_rate_limit(SubscriptionTier.ENTERPRISE, "alerts") == 10000
        assert enforcer.get_rate_limit(SubscriptionTier.ENTERPRISE, "history") == 5000
    
    def test_check_rate_limit_unlimited(self, enforcer):
        """Test rate limit checking with unlimited access."""
        # Enterprise websocket has no numeric limit (unlimited)
        is_allowed, info = enforcer.check_rate_limit(
            "user123", 
            SubscriptionTier.ENTERPRISE, 
            "websocket"
        )
        
        assert is_allowed is True
        assert info["limit"] == "unlimited"
        assert info["remaining"] == "unlimited"
    
    def test_check_rate_limit_within_limit(self, enforcer):
        """Test rate limit checking within limits."""
        user_id = "user123"
        tier = SubscriptionTier.FREE
        endpoint_type = "alerts"
        
        # First request should be allowed
        is_allowed, info = enforcer.check_rate_limit(user_id, tier, endpoint_type)
        
        assert is_allowed is True
        assert info["limit"] == 10
        assert info["remaining"] == 9  # 10 - 1 (current request)
        
        # Make several more requests
        for i in range(8):
            is_allowed, info = enforcer.check_rate_limit(user_id, tier, endpoint_type)
            assert is_allowed is True
        
        # 10th request should still be allowed
        is_allowed, info = enforcer.check_rate_limit(user_id, tier, endpoint_type)
        assert is_allowed is True
        assert info["remaining"] == 0
    
    def test_check_rate_limit_exceeded(self, enforcer):
        """Test rate limit checking when limit is exceeded."""
        user_id = "user123"
        tier = SubscriptionTier.FREE
        endpoint_type = "alerts"
        
        # Make 10 requests (the limit)
        for i in range(10):
            is_allowed, info = enforcer.check_rate_limit(user_id, tier, endpoint_type)
            assert is_allowed is True
        
        # 11th request should be denied
        is_allowed, info = enforcer.check_rate_limit(user_id, tier, endpoint_type)
        assert is_allowed is False
        assert info["limit"] == 10
        assert info["remaining"] == 0
    
    def test_check_rate_limit_window_reset(self, enforcer):
        """Test rate limit window reset."""
        user_id = "user123"
        tier = SubscriptionTier.FREE
        endpoint_type = "alerts"
        window_seconds = 1  # 1 second window for testing
        
        # Make requests up to limit
        for i in range(10):
            is_allowed, info = enforcer.check_rate_limit(
                user_id, tier, endpoint_type, window_seconds
            )
            assert is_allowed is True
        
        # Next request should be denied
        is_allowed, info = enforcer.check_rate_limit(
            user_id, tier, endpoint_type, window_seconds
        )
        assert is_allowed is False
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Request should be allowed again
        is_allowed, info = enforcer.check_rate_limit(
            user_id, tier, endpoint_type, window_seconds
        )
        assert is_allowed is True
    
    @pytest.mark.asyncio
    async def test_get_user_subscription_active(self, enforcer):
        """Test getting active user subscription."""
        mock_subscription = Mock()
        mock_subscription.subscription_end_date = None
        
        with patch('app.middleware.subscription.get_subscriptions_repository') as mock_repo:
            mock_repo.return_value.get_by_user_id = AsyncMock(return_value=mock_subscription)
            
            result = await enforcer.get_user_subscription("user123")
            
            assert result == mock_subscription
            mock_repo.return_value.get_by_user_id.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_get_user_subscription_expired(self, enforcer):
        """Test getting expired user subscription."""
        mock_subscription = Mock()
        mock_subscription.subscription_end_date = datetime.utcnow() - timedelta(days=1)
        mock_subscription.tier = SubscriptionTier.PRO
        
        with patch('app.middleware.subscription.get_subscriptions_repository') as mock_repo:
            mock_repo.return_value.get_by_user_id = AsyncMock(return_value=mock_subscription)
            mock_repo.return_value.update_subscription_tier = AsyncMock(return_value=mock_subscription)
            
            result = await enforcer.get_user_subscription("user123")
            
            # Should downgrade to free tier
            assert result.tier == SubscriptionTier.FREE
            mock_repo.return_value.update_subscription_tier.assert_called_once_with(
                "user123", SubscriptionTier.FREE
            )
    
    @pytest.mark.asyncio
    async def test_get_user_subscription_not_found(self, enforcer):
        """Test getting user subscription when none exists."""
        with patch('app.middleware.subscription.get_subscriptions_repository') as mock_repo:
            mock_repo.return_value.get_by_user_id = AsyncMock(return_value=None)
            
            result = await enforcer.get_user_subscription("user123")
            
            assert result is None


class TestSubscriptionDependencies:
    """Test cases for subscription dependency functions."""
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        return {"id": "user123", "email": "test@example.com"}
    
    @pytest.fixture
    def mock_enforcer(self):
        """Mock subscription enforcer."""
        return Mock()
    
    @pytest.fixture
    def mock_subscription(self):
        """Mock user subscription."""
        subscription = Mock()
        subscription.tier = SubscriptionTier.PRO
        subscription.alert_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        return subscription
    
    @pytest.mark.asyncio
    async def test_require_subscription_tier_success(self, mock_current_user, mock_enforcer, mock_subscription):
        """Test successful tier requirement check."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        
        result = await require_subscription_tier(
            SubscriptionTier.PRO, 
            mock_current_user, 
            mock_enforcer
        )
        
        assert result == mock_subscription
        mock_enforcer.get_user_subscription.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_require_subscription_tier_no_subscription(self, mock_current_user, mock_enforcer):
        """Test tier requirement when no subscription exists."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await require_subscription_tier(
                SubscriptionTier.PRO, 
                mock_current_user, 
                mock_enforcer
            )
        
        assert exc_info.value.status_code == 403
        assert "No subscription found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_subscription_tier_insufficient(self, mock_current_user, mock_enforcer):
        """Test tier requirement with insufficient tier."""
        mock_subscription = Mock()
        mock_subscription.tier = SubscriptionTier.FREE
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        
        with pytest.raises(HTTPException) as exc_info:
            await require_subscription_tier(
                SubscriptionTier.PRO, 
                mock_current_user, 
                mock_enforcer
            )
        
        assert exc_info.value.status_code == 403
        assert "requires pro tier or higher" in exc_info.value.detail
        assert "Current tier: free" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_subscription_tier_hierarchy(self, mock_current_user, mock_enforcer):
        """Test tier hierarchy (enterprise can access pro features)."""
        mock_subscription = Mock()
        mock_subscription.tier = SubscriptionTier.ENTERPRISE
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        
        # Enterprise user should be able to access pro features
        result = await require_subscription_tier(
            SubscriptionTier.PRO, 
            mock_current_user, 
            mock_enforcer
        )
        
        assert result == mock_subscription
    
    @pytest.mark.asyncio
    async def test_require_feature_access_success(self, mock_current_user, mock_enforcer, mock_subscription):
        """Test successful feature access check."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        mock_enforcer.is_feature_allowed = Mock(return_value=True)
        
        result = await require_feature_access(
            "api", 
            mock_current_user, 
            mock_enforcer
        )
        
        assert result == mock_subscription
        mock_enforcer.is_feature_allowed.assert_called_once_with(SubscriptionTier.PRO, "api")
    
    @pytest.mark.asyncio
    async def test_require_feature_access_denied(self, mock_current_user, mock_enforcer, mock_subscription):
        """Test feature access denial."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        mock_enforcer.is_feature_allowed = Mock(return_value=False)
        mock_enforcer.get_tier_config = Mock(return_value={"features": ["dashboard", "api"]})
        
        with pytest.raises(HTTPException) as exc_info:
            await require_feature_access(
                "csv_export", 
                mock_current_user, 
                mock_enforcer
            )
        
        assert exc_info.value.status_code == 403
        assert "Feature 'csv_export' not available" in exc_info.value.detail
        assert "Available features: dashboard, api" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_enforce_rate_limit_success(self, mock_current_user, mock_enforcer, mock_subscription):
        """Test successful rate limit enforcement."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        mock_enforcer.check_rate_limit = Mock(return_value=(True, {
            "limit": 1000,
            "remaining": 999,
            "reset_time": time.time() + 3600,
            "window_seconds": 3600
        }))
        
        result = await enforce_rate_limit(
            "alerts", 
            mock_current_user, 
            mock_enforcer
        )
        
        assert result["limit"] == 1000
        assert result["remaining"] == 999
        mock_enforcer.check_rate_limit.assert_called_once_with("user123", SubscriptionTier.PRO, "alerts")
    
    @pytest.mark.asyncio
    async def test_enforce_rate_limit_exceeded(self, mock_current_user, mock_enforcer, mock_subscription):
        """Test rate limit exceeded."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=mock_subscription)
        mock_enforcer.check_rate_limit = Mock(return_value=(False, {
            "limit": 10,
            "remaining": 0,
            "reset_time": time.time() + 3600,
            "window_seconds": 3600
        }))
        
        with pytest.raises(HTTPException) as exc_info:
            await enforce_rate_limit(
                "alerts", 
                mock_current_user, 
                mock_enforcer
            )
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail
        assert "X-RateLimit-Limit" in exc_info.value.headers
        assert exc_info.value.headers["X-RateLimit-Limit"] == "10"
        assert exc_info.value.headers["X-RateLimit-Remaining"] == "0"
    
    @pytest.mark.asyncio
    async def test_enforce_rate_limit_no_subscription(self, mock_current_user, mock_enforcer):
        """Test rate limit enforcement with no subscription (uses free tier)."""
        mock_enforcer.get_user_subscription = AsyncMock(return_value=None)
        mock_enforcer.check_rate_limit = Mock(return_value=(True, {
            "limit": 10,
            "remaining": 9,
            "reset_time": time.time() + 3600,
            "window_seconds": 3600
        }))
        
        result = await enforce_rate_limit(
            "alerts", 
            mock_current_user, 
            mock_enforcer
        )
        
        assert result["limit"] == 10
        mock_enforcer.check_rate_limit.assert_called_once_with("user123", SubscriptionTier.FREE, "alerts")
    
    @pytest.mark.asyncio
    async def test_get_api_key_subscription_valid(self):
        """Test API key subscription validation with valid key."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_api_key_hash"
        )
        
        mock_subscription = Mock()
        mock_subscription.is_active = True
        mock_subscription.subscription_end_date = None
        
        with patch('app.middleware.subscription.get_subscriptions_repository') as mock_repo:
            mock_repo.return_value.get_by_api_key_hash = AsyncMock(return_value=mock_subscription)
            
            result = await get_api_key_subscription(mock_credentials, Mock())
            
            assert result == mock_subscription
            mock_repo.return_value.get_by_api_key_hash.assert_called_once_with("valid_api_key_hash")
    
    @pytest.mark.asyncio
    async def test_get_api_key_subscription_expired(self):
        """Test API key subscription validation with expired subscription."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="expired_api_key_hash"
        )
        
        mock_subscription = Mock()
        mock_subscription.is_active = True
        mock_subscription.subscription_end_date = datetime.utcnow() - timedelta(days=1)
        
        with patch('app.middleware.subscription.get_subscriptions_repository') as mock_repo:
            mock_repo.return_value.get_by_api_key_hash = AsyncMock(return_value=mock_subscription)
            
            result = await get_api_key_subscription(mock_credentials, Mock())
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_api_key_subscription_no_credentials(self):
        """Test API key subscription validation with no credentials."""
        result = await get_api_key_subscription(None, Mock())
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_api_key_subscription_invalid_key(self):
        """Test API key subscription validation with invalid key."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_api_key_hash"
        )
        
        with patch('app.middleware.subscription.get_subscriptions_repository') as mock_repo:
            mock_repo.return_value.get_by_api_key_hash = AsyncMock(return_value=None)
            
            result = await get_api_key_subscription(mock_credentials, Mock())
            
            assert result is None