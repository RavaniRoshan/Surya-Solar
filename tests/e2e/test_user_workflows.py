"""End-to-end tests for complete user workflows."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

from app.main import create_app
from app.services.auth_service import create_access_token, UserSession
from app.models.core import PredictionResult, SeverityLevel


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


class TestCompleteUserOnboardingWorkflow:
    """Test complete user onboarding workflow from registration to first alert."""
    
    @patch('app.api.auth.auth_service')
    @patch('app.api.payments.razorpay_service')
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @pytest.mark.asyncio
    async def test_complete_user_journey(
        self,
        mock_api_usage_repo,
        mock_predictions_repo,
        mock_razorpay_service,
        mock_auth_service,
        async_client
    ):
        """Test complete user journey from signup to receiving alerts."""
        
        # Step 1: User Registration
        mock_auth_service.sign_up = AsyncMock(return_value={
            "user_id": "new-user-123",
            "email": "newuser@example.com",
            "access_token": "jwt-token-123",
            "subscription_tier": "free"
        })
        
        registration_response = await async_client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "securepassword123"
        })
        
        assert registration_response.status_code == 200
        user_data = registration_response.json()
        assert user_data["user_id"] == "new-user-123"
        assert user_data["subscription_tier"] == "free"
        
        # Step 2: User tries to access alerts (free tier)
        mock_user_session = UserSession(
            user_id="new-user-123",
            email="newuser@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=PredictionResult(
            id="pred-123",
            timestamp=datetime.utcnow(),
            flare_probability=0.65,
            severity_level=SeverityLevel.MEDIUM,
            model_version="surya-1.0"
        ))
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=2)
        mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
        
        alert_response = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": f"Bearer {user_data['access_token']}"}
        )
        
        assert alert_response.status_code == 200
        alert_data = alert_response.json()
        assert alert_data["current_probability"] == 0.65
        
        # Step 3: User upgrades to Pro subscription
        mock_razorpay_service.create_subscription = AsyncMock(return_value={
            "id": "sub_123",
            "status": "created",
            "short_url": "https://rzp.io/i/sub_123"
        })
        
        subscription_response = await async_client.post(
            "/api/v1/payments/subscriptions",
            headers={"Authorization": f"Bearer {user_data['access_token']}"},
            json={"plan": "pro"}
        )
        
        assert subscription_response.status_code == 200
        subscription_data = subscription_response.json()
        assert subscription_data["subscription_id"] == "sub_123"
        
        # Step 4: Simulate webhook activation
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
        
        with patch('app.api.payments.subscriptions_repo') as mock_subscriptions_repo:
            mock_razorpay_service.verify_webhook_signature = AsyncMock(return_value=True)
            mock_subscriptions_repo.update_subscription_status = AsyncMock(return_value=True)
            
            webhook_response = await async_client.post(
                "/api/v1/payments/webhooks/razorpay",
                json=webhook_payload,
                headers={"X-Razorpay-Signature": "valid_signature"}
            )
            
            assert webhook_response.status_code == 200
        
        # Step 5: User generates API key
        mock_auth_service.generate_api_key = AsyncMock(return_value="zc_api_key_123")
        
        api_key_response = await async_client.post(
            "/api/v1/auth/api-key",
            headers={"Authorization": f"Bearer {user_data['access_token']}"}
        )
        
        assert api_key_response.status_code == 200
        api_key_data = api_key_response.json()
        assert api_key_data["api_key"].startswith("zc_")
        
        # Step 6: User accesses alerts with API key
        pro_user_session = UserSession(
            user_id="new-user-123",
            email="newuser@example.com",
            subscription_tier="pro",
            api_key="zc_api_key_123",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_api_key = AsyncMock(return_value=pro_user_session)
        
        api_alert_response = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": f"Bearer {api_key_data['api_key']}"}
        )
        
        assert api_alert_response.status_code == 200
        
        # Step 7: User accesses extended history (Pro feature)
        mock_predictions_repo.get_predictions_by_time_range = AsyncMock(return_value=[
            PredictionResult(
                id=f"pred-{i}",
                timestamp=datetime.utcnow() - timedelta(hours=i),
                flare_probability=0.5 + (i * 0.05),
                severity_level=SeverityLevel.MEDIUM,
                model_version="surya-1.0"
            )
            for i in range(10)
        ])
        
        history_response = await async_client.get(
            "/api/v1/alerts/history?hours_back=48",  # Extended history
            headers={"Authorization": f"Bearer {api_key_data['api_key']}"}
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data["alerts"]) == 10


class TestRealTimeAlertWorkflow:
    """Test real-time alert workflow with WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_websocket_alert_workflow(self, client):
        """Test complete WebSocket alert workflow."""
        with patch('app.api.websocket.auth_service') as mock_auth_service, \
             patch('app.api.websocket.websocket_manager') as mock_ws_manager, \
             patch('app.services.alert_broadcaster.websocket_manager') as mock_broadcaster:
            
            # Setup authenticated user
            mock_user_session = UserSession(
                user_id="ws-user-123",
                email="wsuser@example.com",
                subscription_tier="pro",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            mock_auth_service.validate_token = AsyncMock(return_value=mock_user_session)
            mock_ws_manager.connect = AsyncMock()
            mock_ws_manager.disconnect = AsyncMock()
            mock_ws_manager.send_personal_message = AsyncMock()
            
            # Step 1: Establish WebSocket connection
            with client.websocket_connect("/ws/alerts?token=valid-token") as websocket:
                # Step 2: Send ping to test connection
                websocket.send_json({"type": "ping"})
                
                # Step 3: Receive pong response
                response = websocket.receive_json()
                assert response["type"] == "pong"
                
                # Step 4: Simulate high-severity alert
                alert_message = {
                    "type": "alert",
                    "data": {
                        "flare_probability": 0.92,
                        "severity_level": "high",
                        "timestamp": datetime.utcnow().isoformat(),
                        "alert_triggered": True,
                        "message": "High solar flare probability detected!"
                    }
                }
                
                # Simulate alert broadcast
                websocket.send_json(alert_message)
                
                # Verify connection was established
                mock_ws_manager.connect.assert_called_once()


class TestAPIIntegrationWorkflow:
    """Test API integration workflow for external systems."""
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.api_usage_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_external_system_integration(
        self,
        mock_auth_service,
        mock_api_usage_repo,
        mock_predictions_repo,
        async_client
    ):
        """Test workflow for external system integration."""
        
        # Setup enterprise user
        enterprise_user = UserSession(
            user_id="enterprise-user-123",
            email="enterprise@company.com",
            subscription_tier="enterprise",
            api_key="zc_enterprise_key_123",
            webhook_url="https://company.com/solar-alerts",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_api_key = AsyncMock(return_value=enterprise_user)
        mock_api_usage_repo.get_usage_count = AsyncMock(return_value=50)
        mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
        
        # Step 1: Get current alert
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=PredictionResult(
            id="pred-enterprise-1",
            timestamp=datetime.utcnow(),
            flare_probability=0.88,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0",
            confidence_score=0.92
        ))
        
        current_response = await async_client.get(
            "/api/v1/alerts/current",
            headers={"Authorization": "Bearer zc_enterprise_key_123"}
        )
        
        assert current_response.status_code == 200
        current_data = current_response.json()
        assert current_data["current_probability"] == 0.88
        assert current_data["alert_active"] is True  # Above 0.8 threshold
        
        # Step 2: Get detailed statistics (Enterprise feature)
        mock_predictions_repo.get_prediction_statistics = AsyncMock(return_value={
            "total_predictions": 500,
            "avg_probability": 0.45,
            "max_probability": 0.95,
            "high_severity_count": 25,
            "medium_severity_count": 150,
            "low_severity_count": 325
        })
        
        mock_predictions_repo.get_hourly_prediction_counts = AsyncMock(return_value=[
            {"hour": datetime.utcnow() - timedelta(hours=i), "prediction_count": 10 + i}
            for i in range(24)
        ])
        
        stats_response = await async_client.get(
            "/api/v1/alerts/statistics?hours_back=24",
            headers={"Authorization": "Bearer zc_enterprise_key_123"}
        )
        
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["subscription_tier"] == "enterprise"
        assert "hourly_breakdown" in stats_data["statistics"]
        assert len(stats_data["statistics"]["hourly_breakdown"]) == 24
        
        # Step 3: Get filtered historical data
        mock_predictions_repo.get_predictions_above_threshold = AsyncMock(return_value=[
            PredictionResult(
                id=f"pred-high-{i}",
                timestamp=datetime.utcnow() - timedelta(hours=i),
                flare_probability=0.8 + (i * 0.02),
                severity_level=SeverityLevel.HIGH,
                model_version="surya-1.0"
            )
            for i in range(5)
        ])
        
        history_response = await async_client.get(
            "/api/v1/alerts/history?min_probability=0.8&hours_back=72",
            headers={"Authorization": "Bearer zc_enterprise_key_123"}
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert len(history_data["alerts"]) == 5
        assert all(alert["flare_probability"] >= 0.8 for alert in history_data["alerts"])


class TestErrorRecoveryWorkflow:
    """Test error recovery and resilience workflows."""
    
    @patch('app.api.alerts.predictions_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_service_degradation_workflow(
        self,
        mock_auth_service,
        mock_predictions_repo,
        async_client
    ):
        """Test workflow during service degradation."""
        
        user_session = UserSession(
            user_id="test-user-123",
            email="test@example.com",
            subscription_tier="pro",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=user_session)
        
        # Step 1: Normal operation
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=PredictionResult(
            id="pred-normal",
            timestamp=datetime.utcnow(),
            flare_probability=0.45,
            severity_level=SeverityLevel.MEDIUM,
            model_version="surya-1.0"
        ))
        
        with patch('app.api.alerts.api_usage_repo') as mock_api_usage_repo:
            mock_api_usage_repo.get_usage_count = AsyncMock(return_value=10)
            mock_api_usage_repo.create = AsyncMock(return_value="usage-123")
            
            normal_response = await async_client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer valid-token"}
            )
            
            assert normal_response.status_code == 200
        
        # Step 2: Database error occurs
        mock_predictions_repo.get_current_prediction = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        with patch('app.api.alerts.api_usage_repo') as mock_api_usage_repo:
            mock_api_usage_repo.get_usage_count = AsyncMock(return_value=10)
            
            error_response = await async_client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer valid-token"}
            )
            
            assert error_response.status_code == 500
            assert "Failed to retrieve current alert" in error_response.json()["detail"]
        
        # Step 3: Service recovery
        mock_predictions_repo.get_current_prediction = AsyncMock(return_value=PredictionResult(
            id="pred-recovered",
            timestamp=datetime.utcnow(),
            flare_probability=0.55,
            severity_level=SeverityLevel.MEDIUM,
            model_version="surya-1.0"
        ))
        
        with patch('app.api.alerts.api_usage_repo') as mock_api_usage_repo:
            mock_api_usage_repo.get_usage_count = AsyncMock(return_value=11)
            mock_api_usage_repo.create = AsyncMock(return_value="usage-124")
            
            recovery_response = await async_client.get(
                "/api/v1/alerts/current",
                headers={"Authorization": "Bearer valid-token"}
            )
            
            assert recovery_response.status_code == 200
            recovery_data = recovery_response.json()
            assert recovery_data["current_probability"] == 0.55


class TestSubscriptionLifecycleWorkflow:
    """Test complete subscription lifecycle workflow."""
    
    @patch('app.api.payments.razorpay_service')
    @patch('app.api.payments.subscriptions_repo')
    @patch('app.api.alerts.auth_service')
    @pytest.mark.asyncio
    async def test_subscription_lifecycle(
        self,
        mock_auth_service,
        mock_subscriptions_repo,
        mock_razorpay_service,
        async_client
    ):
        """Test complete subscription lifecycle from creation to cancellation."""
        
        user_session = UserSession(
            user_id="lifecycle-user-123",
            email="lifecycle@example.com",
            subscription_tier="free",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        mock_auth_service.validate_token = AsyncMock(return_value=user_session)
        
        # Step 1: Create subscription
        mock_razorpay_service.create_subscription = AsyncMock(return_value={
            "id": "sub_lifecycle_123",
            "status": "created",
            "short_url": "https://rzp.io/i/sub_lifecycle_123"
        })
        
        create_response = await async_client.post(
            "/api/v1/payments/subscriptions",
            headers={"Authorization": "Bearer valid-token"},
            json={"plan": "pro"}
        )
        
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["subscription_id"] == "sub_lifecycle_123"
        
        # Step 2: Subscription activation webhook
        mock_razorpay_service.verify_webhook_signature = AsyncMock(return_value=True)
        mock_subscriptions_repo.update_subscription_status = AsyncMock(return_value=True)
        
        activation_payload = {
            "event": "subscription.activated",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_lifecycle_123",
                        "status": "active"
                    }
                }
            }
        }
        
        activation_response = await async_client.post(
            "/api/v1/payments/webhooks/razorpay",
            json=activation_payload,
            headers={"X-Razorpay-Signature": "valid_signature"}
        )
        
        assert activation_response.status_code == 200
        
        # Step 3: Subscription upgrade
        mock_razorpay_service.update_subscription = AsyncMock(return_value={
            "id": "sub_lifecycle_123",
            "status": "active",
            "plan_id": "enterprise_plan"
        })
        
        upgrade_response = await async_client.put(
            "/api/v1/payments/subscriptions/sub_lifecycle_123",
            headers={"Authorization": "Bearer valid-token"},
            json={"plan": "enterprise"}
        )
        
        assert upgrade_response.status_code == 200
        
        # Step 4: Subscription cancellation
        mock_razorpay_service.cancel_subscription = AsyncMock(return_value={
            "id": "sub_lifecycle_123",
            "status": "cancelled"
        })
        
        cancel_response = await async_client.delete(
            "/api/v1/payments/subscriptions/sub_lifecycle_123",
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert cancel_response.status_code == 200
        
        # Step 5: Cancellation webhook
        cancellation_payload = {
            "event": "subscription.cancelled",
            "payload": {
                "subscription": {
                    "entity": {
                        "id": "sub_lifecycle_123",
                        "status": "cancelled"
                    }
                }
            }
        }
        
        cancellation_response = await async_client.post(
            "/api/v1/payments/webhooks/razorpay",
            json=cancellation_payload,
            headers={"X-Razorpay-Signature": "valid_signature"}
        )
        
        assert cancellation_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])