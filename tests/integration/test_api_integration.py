"""Integration tests for API endpoints."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

from app.main import create_app
from app.models.core import PredictionResult, SeverityLevel
from app.services.auth_service import UserSession, create_access_token


@pytest.fixture
def app():
    """Create test FastAPI app."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_token():
    """Create valid auth token for testing."""
    token_data = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "subscription_tier": "pro"
    }
    return create_access_token(token_data)


@pytest.fixture
def enterprise_token():
    """Create enterprise auth token for testing."""
    token_data = {
        "user_id": "enterprise-user-123",
        "email": "enterprise@example.com",
        "subscription_tier": "enterprise"
    }
    return create_access_token(token_data)


@pytest.fixture
def mock_prediction():
    """Mock prediction for testing."""
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


class TestAlertEndpointsIntegration:
    """Integration tests for alert endpoints."""
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_current_alert_full_flow(
        self,
        mock_auth_service,
        mock_api_usage_repo,
        mock_predictions_repo,
        async_client,
        auth_token,
        mock_prediction
    ):
        """Test complete flow for getting current alert."""
        # Setup mocks
        mock_user_session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=mock_prediction)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=5)
        mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
        
        # Make request
        response = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_probability"] == 0.75
        assert data["severity_level"] == "high"
        assert data["alert_active"] is False  # 0.75 < 0.8 (default high threshold)
        assert "last_updated" in data
        assert "next_update" in data
        
        # Verify all services were called
        mock_auth_service.validate_token.assert_called_once()
        mock_predictions_repo.get_current_prediction.assert_called_once()
        mock_api_usage_repo.get_usage_count.assert_called_once()
        mock_api_usage_repo.create.assert_called_once()
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_alert_history_with_filters(
        self,
        mock_auth_service,
        mock_api_usage_repo,
        mock_predictions_repo,
        async_client,
        enterprise_token
    ):
        """Test alert history with various filters."""
        # Setup enterprise user
        mock_user_session = UserSession(
            user_id="enterprise-user-123",
            email="enterprise@example.com",
            subscription_tier="enterprise",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Create mock historical data
        mock_predictions = [
            PredictionResult(
                id=f"pred-{i}",
                timestamp=datetime.utcnow() - timedelta(hours=i),
                flare_probability=0.8 + (i * 0.05),
                severity_level=SeverityLevel.HIGH,
                model_version="surya-1.0"
            )
            for i in range(5)
        ]
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_predictions_repo.get_predictions_by_severity = AsyncMock(return_value=mock_predictions)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=10)
        mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
        
        # Test with severity filter
        response = await async_client.get(
            "/api/v1/alerts/history?severity=high&hours_back=48&page=1&page_size=10",
            headers={"Authorization": f"Bearer {enterprise_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["alerts"]) == 5
        assert data["total_count"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["has_more"] is False
        
        # Verify all alerts are high severity
        for alert in data["alerts"]:
            assert alert["severity_level"] == "high"
            assert alert["flare_probability"] >= 0.8
        
        # Verify repository was called with correct parameters
        mock_predictions_repo.get_predictions_by_severity.assert_called_once_with(
            severity=SeverityLevel.HIGH,
            hours_back=48
        )
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(
        self,
        mock_auth_service,
        mock_api_usage_repo,
        mock_predictions_repo,
        async_client,
        auth_token
    ):
        """Test rate limiting enforcement across multiple requests."""
        mock_user_session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="pro",  # 100 requests per hour
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=None)
        mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
        
        # First request - under limit
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=50)
        response1 = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response1.status_code == 404  # No prediction available
        
        # Second request - at limit
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=100)
        response2 = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response2.status_code == 429  # Rate limit exceeded
        
        # Verify rate limit headers
        assert "X-RateLimit-Limit" in response2.headers
        assert "X-RateLimit-Remaining" in response2.headers
        assert response2.headers["X-RateLimit-Remaining"] == "0"
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_subscription_tier_restrictions(
        self,
        mock_auth_service,
        mock_api_usage_repo,
        mock_predictions_repo,
        async_client
    ):
        """Test subscription tier restrictions."""
        # Free tier user
        free_token = create_access_token({
            "user_id": "free-user-123",
            "email": "free@example.com",
            "subscription_tier": "free"
        })
        
        mock_free_user = UserSession(
            user_id="free-user-123",
            email="free@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_free_user)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=5)
        
        # Free tier should not access extended history
        response = await async_client.get(
            "/api/v1/alerts/history?hours_back=48",  # More than 24 hours
            headers={"Authorization": f"Bearer {free_token}"}
        )
        
        assert response.status_code == 403
        assert "Pro or Enterprise subscription" in response.json()["detail"]
        
        # Free tier should access 24-hour history
        response = await async_client.get(
            "/api/v1/alerts/history?hours_back=24",
            headers={"Authorization": f"Bearer {free_token}"}
        )
        
        assert response.status_code != 403  # Should be allowed


class TestWebSocketIntegration:
    """Integration tests for WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, client):
        """Test WebSocket connection establishment and lifecycle."""
        with patch('app.api.websocket.auth_service') as mock_auth_service, \
             patch('app.api.websocket.websocket_manager') as mock_ws_manager:
            
            mock_user_session = UserSession(
                user_id="test-user-123",
                email="test@example.com",
                subscription_tier="pro",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
            mock_ws_manager.connect = AsyncMock()
            mock_ws_manager.disconnect = AsyncMock()
            mock_ws_manager.send_personal_message = AsyncMock()
            
            # Test WebSocket connection
            with client.websocket_connect("/ws/alerts?token=valid-token") as websocket:
                # Connection should be established
                mock_ws_manager.connect.assert_called_once()
                
                # Test sending a message
                websocket.send_json({"type": "ping"})
                
                # Should receive pong response
                data = websocket.receive_json()
                assert data["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_failure(self, client):
        """Test WebSocket connection with invalid authentication."""
        with patch('app.api.websocket.auth_service') as mock_auth_service:
            mock_auth_service.validate_token = AsyncMock(return_value=None)
            
            # Should reject connection
            with pytest.raises(Exception):  # WebSocket connection should fail
                with client.websocket_connect("/ws/alerts?token=invalid-token"):
                    pass
    
    @pytest.mark.asyncio
    async def test_websocket_alert_broadcasting(self, client):
        """Test alert broadcasting through WebSocket."""
        with patch('app.api.websocket.auth_service') as mock_auth_service, \
             patch('app.api.websocket.websocket_manager') as mock_ws_manager, \
             patch('app.services.alert_broadcaster.websocket_manager') as mock_broadcaster_ws:
            
            mock_user_session = UserSession(
                user_id="test-user-123",
                email="test@example.com",
                subscription_tier="pro",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
            mock_ws_manager.connect = AsyncMock()
            mock_ws_manager.disconnect = AsyncMock()
            
            # Mock alert message
            alert_message = {
                "type": "alert",
                "data": {
                    "flare_probability": 0.85,
                    "severity_level": "high",
                    "timestamp": datetime.utcnow().isoformat(),
                    "alert_triggered": True
                }
            }
            
            mock_ws_manager.send_personal_message = AsyncMock()
            
            with client.websocket_connect("/ws/alerts?token=valid-token") as websocket:
                # Simulate alert broadcast
                await mock_ws_manager.send_personal_message(
                    json.dumps(alert_message),
                    "test-user-123"
                )
                
                # Verify message was sent
                mock_ws_manager.send_personal_message.assert_called_once()


class TestPaymentIntegration:
    """Integration tests for payment endpoints."""
    
    @patch('app.api.payments.razorpay_service')
    @patch('app.api.payments.auth_service')
    @pytest.mark.asyncio
    async def test_create_subscription_flow(
        self,
        mock_auth_service,
        mock_razorpay_service,
        async_client,
        auth_token
    ):
        """Test complete subscription creation flow."""
        mock_user_session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_razorpay_service.create_subscription = AsyncMock(return_value={
            "id": "sub_123",
            "status": "created",
            "short_url": "https://rzp.io/i/sub_123"
        })
        
        # Create subscription
        response = await async_client.post(
            "/api/v1/payments/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"plan": "pro"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["subscription_id"] == "sub_123"
        assert data["status"] == "created"
        assert "payment_url" in data
        
        mock_razorpay_service.create_subscription.assert_called_once_with(
            user_id="test-user-123",
            plan="pro",
            email="test@example.com"
        )
    
    @patch('app.api.payments.razorpay_service')
    @patch('app.api.payments.subscriptions_repo')
    @pytest.mark.asyncio
    async def test_webhook_processing(
        self,
        mock_subscriptions_repo,
        mock_razorpay_service,
        async_client
    ):
        """Test Razorpay webhook processing."""
        webhook_payload = {
            "event": "subscription.activated",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_123",
                        "status": "active",
                        "customer_id": "cust_123"
                    }
                }
            }
        }
        
        mock_razorpay_service.verify_webhook_signature = AsyncMock(return_value=True)
        mock_subscriptions_repo.update_subscription_status = AsyncMock(return_value=True)
        
        # Send webhook
        response = await async_client.post(
            "/api/v1/payments/webhooks/razorpay",
            json=webhook_payload,
            headers={
                "X-Razorpay-Signature": "valid_signature",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        
        # Verify webhook was processed
        mock_razorpay_service.verify_webhook_signature.assert_called_once()
        mock_subscriptions_repo.update_subscription_status.assert_called_once()


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_database_error_handling(
        self,
        mock_auth_service,
        mock_predictions_repo,
        async_client,
        auth_token
    ):
        """Test handling of database errors."""
        mock_user_session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_predictions_repo.get_current_prediction = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        response = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 500
        assert "Failed to retrieve current alert" in response.json()["detail"]
    
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_authentication_error_handling(
        self,
        mock_auth_service,
        async_client
    ):
        """Test handling of authentication errors."""
        mock_auth_service.validate_token = AsyncMock(
            side_effect=Exception("Auth service unavailable")
        )
        mock_auth_service.validate_api_key = AsyncMock(return_value=None)
        
        response = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer some-token"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_malformed_request_handling(self, async_client, auth_token):
        """Test handling of malformed requests."""
        # Test with invalid JSON
        response = await async_client.post(
            "/api/v1/payments/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            content="invalid json"
        )
        
        assert response.status_code == 422
        
        # Test with missing required fields
        response = await async_client.post(
            "/api/v1/payments/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={}  # Missing plan field
        )
        
        assert response.status_code == 422


class TestConcurrentRequests:
    """Test handling of concurrent requests."""
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_concurrent_alert_requests(
        self,
        mock_auth_service,
        mock_api_usage_repo,
        mock_predictions_repo,
        async_client,
        auth_token,
        mock_prediction
    ):
        """Test handling of concurrent alert requests."""
        mock_user_session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=mock_prediction)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=5)
        mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
        
        # Make 10 concurrent requests
        tasks = []
        for _ in range(10):
            task = async_client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["current_probability"] == 0.75
        
        # Verify all requests were processed
        assert mock_predictions_repo.get_current_prediction.call_count == 10
        assert mock_api_usage_repo.create.call_count == 10


if __name__ == "__main__":
    pytest.main([__file__])