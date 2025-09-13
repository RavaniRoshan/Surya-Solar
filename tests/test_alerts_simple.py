"""Simple test for alert endpoints to verify basic functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.core import PredictionResult, SeverityLevel
from app.services.auth_service import UserSession


def test_health_endpoint():
    """Test that the health endpoint works."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test that the root endpoint works."""
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


@patch('app.api.alerts.auth_service')
@patch('app.api.alerts.predictions_repo')
@patch('app.api.alerts.api_usage_repo')
def test_current_alert_unauthorized(mock_api_usage_repo, mock_predictions_repo, mock_auth_service):
    """Test unauthorized access returns 401."""
    app = create_app()
    client = TestClient(app)
    
    # Mock auth failure
    mock_auth_service.validate_token = AsyncMock(return_value=None)
    mock_auth_service.validate_api_key = AsyncMock(return_value=None)
    
    response = client.get("/api/v1/alerts/current")
    assert response.status_code == 403  # No auth header


@patch('app.api.alerts.auth_service')
@patch('app.api.alerts.predictions_repo')
@patch('app.api.alerts.api_usage_repo')
def test_current_alert_success(mock_api_usage_repo, mock_predictions_repo, mock_auth_service):
    """Test successful current alert retrieval."""
    app = create_app()
    client = TestClient(app)
    
    # Mock user session
    mock_user = UserSession(
        user_id="test-user",
        email="test@example.com",
        subscription_tier="pro",
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    # Mock prediction
    mock_prediction = PredictionResult(
        id="test-pred",
        timestamp=datetime.utcnow(),
        flare_probability=0.75,
        severity_level=SeverityLevel.HIGH,
        model_version="surya-1.0"
    )
    
    # Setup mocks
    mock_auth_service.validate_token = AsyncMock(return_value=mock_user)
    mock_predictions_repo.get_current_prediction = AsyncMock(return_value=mock_prediction)
    mock_api_usage_repo.get_usage_count = AsyncMock(return_value=5)
    mock_api_usage_repo.create = AsyncMock(return_value=None)
    
    response = client.get(
        "/api/v1/alerts/current",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "current_probability" in data
    assert "severity_level" in data
    assert "last_updated" in data
    assert "next_update" in data
    assert "alert_active" in data


if __name__ == "__main__":
    pytest.main([__file__])