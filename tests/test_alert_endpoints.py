"""Tests for alert API endpoints."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import create_app
from app.models.core import (
    PredictionResult, 
    SeverityLevel,
    SubscriptionTier
)
from app.services.auth_service import AuthService, UserSession


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
        api_key="test-api-key",
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_prediction():
    """Mock prediction result for testing."""
    return PredictionResult(
        id="pred-123",
        timestamp=datetime.utcnow(),
        flare_probability=0.75,
        severity_level=SeverityLevel.HIGH,
        model_version="surya-1.0",
        confidence_score=0.85,
        raw_output={"test": "data"},
        solar_data={"magnetic_field": [1.0, 2.0, 3.0]}
    )


class TestCurrentAlertEndpoint:
    """Test cases for GET /api/v1/alerts/current endpoint."""
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_current_alert_success(
        self, 
        mock_api_usage_repo,
        mock_predictions_repo, 
        mock_auth_service,
        client,
        mock_user_session,
        mock_prediction
    ):
        """Test successful current alert retrieval."""
        # Setup mocks
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=mock_prediction)
        mock_api_usage_repo.create = AsyncMock(return_value=None)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=5)  # Under rate limit
        
        # Make request
        response = client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["current_probability"] == 0.75
        assert data["severity_level"] == "high"
        assert data["alert_active"] is True  # Above default high threshold (0.8)
        assert "last_updated" in data
        assert "next_update" in data
    
    @patch('app.api.alerts.auth_service')
    def test_get_current_alert_unauthorized(self, mock_auth_service, client):
        """Test unauthorized access to current alert."""
        mock_auth_service.validate_token = AsyncMock(return_value=None)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        
        response = client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_current_alert_no_prediction(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test current alert when no prediction available."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=None)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=5)
        
        response = client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No current prediction available" in response.json()["detail"]
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_current_alert_rate_limit_exceeded(
        self,
        mock_api_usage_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test rate limit exceeded for current alert."""
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=1000)  # Exceeds pro tier limit
        
        response = client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Rate limit exceeded" in response.json()["detail"]
        assert "X-RateLimit-Limit" in response.headers


class TestHistoryAlertEndpoint:
    """Test cases for GET /api/v1/alerts/history endpoint."""
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_alert_history_success(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test successful alert history retrieval."""
        # Create mock predictions
        mock_predictions = [
            PredictionResult(
                id=f"pred-{i}",
                timestamp=datetime.utcnow() - timedelta(hours=i),
                flare_probability=0.5 + (i * 0.1),
                severity_level=SeverityLevel.MEDIUM,
                model_version="surya-1.0"
            )
            for i in range(5)
        ]
        
        mock_auth_service.validate_token.return_value = mock_user_session
        mock_predictions_repo.get_predictions_by_time_range.return_value = mock_predictions
        mock_api_usage_repo.get_usage_count.return_value = 5
        
        response = client.get(
            "/api/v1/alerts/history?hours_back=24&page=1&page_size=10",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["alerts"]) == 5
        assert data["total_count"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["has_more"] is False
        
        # Check alert structure
        alert = data["alerts"][0]
        assert "id" in alert
        assert "timestamp" in alert
        assert "flare_probability" in alert
        assert "severity_level" in alert
        assert "alert_triggered" in alert
        assert "message" in alert
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_alert_history_with_severity_filter(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test alert history with severity filter."""
        mock_high_predictions = [
            PredictionResult(
                id="pred-high-1",
                timestamp=datetime.utcnow(),
                flare_probability=0.9,
                severity_level=SeverityLevel.HIGH,
                model_version="surya-1.0"
            )
        ]
        
        mock_auth_service.validate_token.return_value = mock_user_session
        mock_predictions_repo.get_predictions_by_severity.return_value = mock_high_predictions
        mock_api_usage_repo.get_usage_count.return_value = 5
        
        response = client.get(
            "/api/v1/alerts/history?severity=high",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["severity_level"] == "high"
        
        # Verify correct repository method was called
        mock_predictions_repo.get_predictions_by_severity.assert_called_once_with(
            severity=SeverityLevel.HIGH,
            hours_back=24  # default
        )
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_alert_history_with_probability_filter(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test alert history with minimum probability filter."""
        mock_high_prob_predictions = [
            PredictionResult(
                id="pred-prob-1",
                timestamp=datetime.utcnow(),
                flare_probability=0.85,
                severity_level=SeverityLevel.HIGH,
                model_version="surya-1.0"
            )
        ]
        
        mock_auth_service.validate_token.return_value = mock_user_session
        mock_predictions_repo.get_predictions_above_threshold.return_value = mock_high_prob_predictions
        mock_api_usage_repo.get_usage_count.return_value = 5
        
        response = client.get(
            "/api/v1/alerts/history?min_probability=0.8",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["flare_probability"] == 0.85
        
        # Verify correct repository method was called
        mock_predictions_repo.get_predictions_above_threshold.assert_called_once_with(
            probability_threshold=0.8,
            hours_back=24
        )
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_alert_history_free_tier_restriction(
        self,
        mock_api_usage_repo,
        mock_auth_service,
        client
    ):
        """Test free tier restriction for extended history."""
        free_user = UserSession(
            user_id="free-user",
            email="free@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token.return_value = free_user
        mock_api_usage_repo.get_usage_count.return_value = 2
        
        response = client.get(
            "/api/v1/alerts/history?hours_back=48",  # More than 24 hours
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Pro or Enterprise subscription" in response.json()["detail"]
    
    def test_get_alert_history_pagination(self, client):
        """Test pagination parameters validation."""
        with patch('app.api.alerts.auth_service') as mock_auth_service:
            mock_auth_service.validate_token.return_value = UserSession(
                user_id="test-user",
                email="test@example.com",
                subscription_tier="pro",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Test invalid page number
            response = client.get(
                "/api/v1/alerts/history?page=0",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            # Test invalid page size
            response = client.get(
                "/api/v1/alerts/history?page_size=101",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAlertStatisticsEndpoint:
    """Test cases for GET /api/v1/alerts/statistics endpoint."""
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_alert_statistics_basic(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test basic alert statistics for non-enterprise user."""
        mock_stats = {
            "total_predictions": 100,
            "avg_probability": 0.45,
            "max_probability": 0.95,
            "min_probability": 0.05,
            "high_severity_count": 10,
            "medium_severity_count": 30,
            "low_severity_count": 60
        }
        
        mock_auth_service.validate_token.return_value = mock_user_session
        mock_predictions_repo.get_prediction_statistics.return_value = mock_stats
        mock_api_usage_repo.get_usage_count.return_value = 5
        
        response = client.get(
            "/api/v1/alerts/statistics",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["statistics"] == mock_stats
        assert data["time_period_hours"] == 24
        assert data["subscription_tier"] == "pro"
        assert "hourly_breakdown" not in data["statistics"]  # Not enterprise
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_get_alert_statistics_enterprise(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client
    ):
        """Test enhanced statistics for enterprise user."""
        enterprise_user = UserSession(
            user_id="enterprise-user",
            email="enterprise@example.com",
            subscription_tier="enterprise",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_stats = {"total_predictions": 100}
        mock_hourly = [{"hour": datetime.utcnow(), "prediction_count": 10}]
        
        mock_auth_service.validate_token.return_value = enterprise_user
        mock_predictions_repo.get_prediction_statistics.return_value = mock_stats
        mock_predictions_repo.get_hourly_prediction_counts.return_value = mock_hourly
        mock_api_usage_repo.get_usage_count.return_value = 5
        
        response = client.get(
            "/api/v1/alerts/statistics",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["subscription_tier"] == "enterprise"
        assert "hourly_breakdown" in data["statistics"]
        assert data["statistics"]["hourly_breakdown"] == mock_hourly


class TestAuthenticationAndRateLimiting:
    """Test authentication and rate limiting functionality."""
    
    @patch('app.api.alerts.auth_service')
    def test_api_key_authentication(self, mock_auth_service, client, mock_user_session):
        """Test API key authentication."""
        mock_auth_service.validate_token.return_value = None  # JWT fails
        mock_auth_service.validate_api_key.return_value = mock_user_session  # API key succeeds
        
        with patch('app.api.alerts.predictions_repo') as mock_predictions_repo, \
             patch('app.api.alerts.api_usage_repo') as mock_api_usage_repo:
            
            mock_predictions_repo.get_current_prediction.return_value = PredictionResult(
                id="test",
                timestamp=datetime.utcnow(),
                flare_probability=0.5,
                severity_level=SeverityLevel.MEDIUM,
                model_version="surya-1.0"
            )
            mock_api_usage_repo.get_usage_count.return_value = 5
            
            response = client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer api-key-123"}
            )
            
            assert response.status_code == status.HTTP_200_OK
            mock_auth_service.validate_api_key.assert_called_once_with("api-key-123")
    
    def test_missing_authorization_header(self, client):
        """Test request without authorization header."""
        response = client.get("/api/v1/alerts/current")
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.api_usage_repo')
    def test_rate_limiting_different_tiers(self, mock_api_usage_repo, mock_auth_service, client):
        """Test rate limiting for different subscription tiers."""
        # Test free tier rate limit
        free_user = UserSession(
            user_id="free-user",
            email="free@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token.return_value = free_user
        mock_api_usage_repo.get_usage_count.return_value = 10  # At free tier limit
        
        response = client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Free tier allows 10 alerts requests per hour" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('app.api.alerts.auth_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    def test_database_error_handling(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_auth_service,
        client,
        mock_user_session
    ):
        """Test handling of database errors."""
        mock_auth_service.validate_token.return_value = mock_user_session
        mock_predictions_repo.get_current_prediction.side_effect = Exception("Database error")
        mock_api_usage_repo.get_usage_count.return_value = 5
        
        response = client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve current alert" in response.json()["detail"]
    
    def test_invalid_query_parameters(self, client):
        """Test validation of query parameters."""
        with patch('app.api.alerts.auth_service') as mock_auth_service:
            mock_auth_service.validate_token.return_value = UserSession(
                user_id="test-user",
                email="test@example.com",
                subscription_tier="pro",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Test invalid hours_back (too high)
            response = client.get(
                "/api/v1/alerts/history?hours_back=200",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            # Test invalid probability range
            response = client.get(
                "/api/v1/alerts/history?min_probability=1.5",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


if __name__ == "__main__":
    pytest.main([__file__])