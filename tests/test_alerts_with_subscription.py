"""Tests for alerts API with subscription enforcement."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.main import create_app
from app.models.core import SubscriptionTier, SeverityLevel


class TestAlertsAPIWithSubscription:
    """Test cases for alerts API with subscription enforcement."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        return {"id": "user123", "email": "test@example.com"}
    
    @pytest.fixture
    def mock_free_subscription(self):
        """Mock free tier subscription."""
        subscription = Mock()
        subscription.tier = SubscriptionTier.FREE
        subscription.alert_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        return subscription
    
    @pytest.fixture
    def mock_pro_subscription(self):
        """Mock pro tier subscription."""
        subscription = Mock()
        subscription.tier = SubscriptionTier.PRO
        subscription.alert_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        return subscription
    
    @pytest.fixture
    def mock_enterprise_subscription(self):
        """Mock enterprise tier subscription."""
        subscription = Mock()
        subscription.tier = SubscriptionTier.ENTERPRISE
        subscription.alert_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
        return subscription
    
    @pytest.fixture
    def mock_prediction(self):
        """Mock prediction result."""
        prediction = Mock()
        prediction.id = "pred123"
        prediction.timestamp = datetime.utcnow()
        prediction.flare_probability = 0.75
        prediction.severity_level = SeverityLevel.HIGH
        prediction.model_version = "surya-1.0"
        prediction.confidence_score = 0.9
        return prediction
    
    def test_get_current_alert_success_pro_tier(self, client, mock_current_user, mock_pro_subscription, mock_prediction):
        """Test successful current alert retrieval with Pro tier."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_pro_subscription), \
             patch('app.api.alerts.enforce_alerts_rate_limit', return_value={"limit": 1000, "remaining": 999}), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_repo.get_current_prediction = AsyncMock(return_value=mock_prediction)
            
            response = client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["current_probability"] == 0.75
            assert data["severity_level"] == "high"
            assert data["alert_active"] is False  # 0.75 < 0.8 threshold
    
    def test_get_current_alert_free_tier_no_api_access(self, client, mock_current_user, mock_free_subscription):
        """Test current alert access denied for free tier (no API access)."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access') as mock_require_api:
            
            # Mock feature access denial
            from fastapi import HTTPException
            mock_require_api.side_effect = HTTPException(
                status_code=403,
                detail="Feature 'api' not available in free tier"
            )
            
            response = client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 403
            assert "not available in free tier" in response.json()["detail"]
    
    def test_get_current_alert_rate_limit_exceeded(self, client, mock_current_user, mock_pro_subscription):
        """Test current alert with rate limit exceeded."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_pro_subscription), \
             patch('app.api.alerts.enforce_alerts_rate_limit') as mock_rate_limit:
            
            # Mock rate limit exceeded
            from fastapi import HTTPException
            mock_rate_limit.side_effect = HTTPException(
                status_code=429,
                detail="Rate limit exceeded for alerts",
                headers={
                    "X-RateLimit-Limit": "1000",
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "3600"
                }
            )
            
            response = client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]
            assert response.headers["X-RateLimit-Limit"] == "1000"
            assert response.headers["X-RateLimit-Remaining"] == "0"
    
    def test_get_alert_history_success_pro_tier(self, client, mock_current_user, mock_pro_subscription, mock_prediction):
        """Test successful alert history retrieval with Pro tier."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_pro_subscription), \
             patch('app.api.alerts.enforce_history_rate_limit', return_value={"limit": 500, "remaining": 499}), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_repo.get_predictions_by_time_range = AsyncMock(return_value=[mock_prediction])
            
            response = client.get(
                "/api/v1/alerts/history?hours_back=24&page=1&page_size=10",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_count"] == 1
            assert data["page"] == 1
            assert data["page_size"] == 10
            assert len(data["alerts"]) == 1
            assert data["alerts"][0]["flare_probability"] == 0.75
    
    def test_get_alert_history_free_tier_extended_period(self, client, mock_current_user, mock_free_subscription):
        """Test alert history with free tier trying to access extended period."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_free_subscription), \
             patch('app.api.alerts.enforce_history_rate_limit', return_value={"limit": 5, "remaining": 4}):
            
            response = client.get(
                "/api/v1/alerts/history?hours_back=48",  # More than 24 hours
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 403
            assert "beyond 24 hours requires Pro or Enterprise" in response.json()["detail"]
    
    def test_get_alert_history_enterprise_extended_period(self, client, mock_current_user, mock_enterprise_subscription, mock_prediction):
        """Test alert history with enterprise tier accessing extended period."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_enterprise_subscription), \
             patch('app.api.alerts.enforce_history_rate_limit', return_value={"limit": 5000, "remaining": 4999}), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_repo.get_predictions_by_time_range = AsyncMock(return_value=[mock_prediction])
            
            response = client.get(
                "/api/v1/alerts/history?hours_back=168",  # 7 days
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 1
    
    def test_get_alert_statistics_basic(self, client, mock_current_user, mock_pro_subscription):
        """Test alert statistics for Pro tier."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_pro_subscription), \
             patch('app.api.alerts.enforce_alerts_rate_limit', return_value={"limit": 1000, "remaining": 999}), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_stats = {
                "total_predictions": 100,
                "high_severity_count": 10,
                "average_probability": 0.45
            }
            mock_repo.get_prediction_statistics = AsyncMock(return_value=mock_stats)
            
            response = client.get(
                "/api/v1/alerts/statistics?hours_back=24",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["statistics"]["total_predictions"] == 100
            assert data["subscription_tier"] == "pro"
            assert "hourly_breakdown" not in data["statistics"]  # Pro tier doesn't get this
    
    def test_get_alert_statistics_enterprise_detailed(self, client, mock_current_user, mock_enterprise_subscription):
        """Test alert statistics for Enterprise tier with detailed breakdown."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access', return_value=mock_enterprise_subscription), \
             patch('app.api.alerts.enforce_alerts_rate_limit', return_value={"limit": 10000, "remaining": 9999}), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_stats = {
                "total_predictions": 100,
                "high_severity_count": 10,
                "average_probability": 0.45
            }
            mock_hourly_counts = [
                {"hour": "2024-01-01T00:00:00Z", "count": 6},
                {"hour": "2024-01-01T01:00:00Z", "count": 6}
            ]
            
            mock_repo.get_prediction_statistics = AsyncMock(return_value=mock_stats)
            mock_repo.get_hourly_prediction_counts = AsyncMock(return_value=mock_hourly_counts)
            
            response = client.get(
                "/api/v1/alerts/statistics?hours_back=24",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["statistics"]["total_predictions"] == 100
            assert data["subscription_tier"] == "enterprise"
            assert "hourly_breakdown" in data["statistics"]
            assert len(data["statistics"]["hourly_breakdown"]) == 2
    
    def test_export_alerts_csv_enterprise_success(self, client, mock_current_user, mock_enterprise_subscription, mock_prediction):
        """Test CSV export success for Enterprise tier."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_enterprise_tier', return_value=mock_enterprise_subscription), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_repo.get_predictions_by_time_range = AsyncMock(return_value=[mock_prediction])
            
            response = client.get(
                "/api/v1/alerts/export/csv?hours_back=168",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment" in response.headers["content-disposition"]
            
            # Check CSV content
            csv_content = response.content.decode('utf-8')
            assert "timestamp,flare_probability,severity_level" in csv_content
            assert "0.75,high,surya-1.0" in csv_content
    
    def test_export_alerts_csv_pro_tier_denied(self, client, mock_current_user, mock_pro_subscription):
        """Test CSV export denied for Pro tier."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_enterprise_tier') as mock_require_enterprise:
            
            # Mock enterprise tier requirement failure
            from fastapi import HTTPException
            mock_require_enterprise.side_effect = HTTPException(
                status_code=403,
                detail="This feature requires enterprise tier or higher. Current tier: pro"
            )
            
            response = client.get(
                "/api/v1/alerts/export/csv?hours_back=168",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 403
            assert "requires enterprise tier" in response.json()["detail"]
    
    def test_export_alerts_csv_with_filters(self, client, mock_current_user, mock_enterprise_subscription, mock_prediction):
        """Test CSV export with filters."""
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_enterprise_tier', return_value=mock_enterprise_subscription), \
             patch('app.api.alerts.predictions_repo') as mock_repo:
            
            mock_repo.get_predictions_by_severity = AsyncMock(return_value=[mock_prediction])
            
            response = client.get(
                "/api/v1/alerts/export/csv?hours_back=24&severity=high&min_probability=0.7",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            
            # Verify the correct repository method was called
            mock_repo.get_predictions_by_severity.assert_called_once_with(
                severity=SeverityLevel.HIGH,
                hours_back=24
            )
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        # No authorization header
        response = client.get("/api/v1/alerts/current")
        assert response.status_code == 401
        
        # Invalid token
        with patch('app.api.alerts.get_current_user') as mock_auth:
            from fastapi import HTTPException
            mock_auth.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            response = client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401
    
    def test_subscription_tier_upgrade_scenarios(self, client, mock_current_user):
        """Test different subscription tier upgrade scenarios."""
        # Free tier trying to access API
        mock_free_sub = Mock()
        mock_free_sub.tier = SubscriptionTier.FREE
        
        with patch('app.api.alerts.get_current_user', return_value=mock_current_user), \
             patch('app.api.alerts.require_api_access') as mock_require_api:
            
            from fastapi import HTTPException
            mock_require_api.side_effect = HTTPException(
                status_code=403,
                detail="Feature 'api' not available in free tier. Available features: dashboard"
            )
            
            response = client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 403
            detail = response.json()["detail"]
            assert "not available in free tier" in detail
            assert "Available features: dashboard" in detail