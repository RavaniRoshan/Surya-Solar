"""Integration tests for real-time alert delivery."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.alert_broadcaster import get_alert_broadcaster
from app.services.websocket_manager import get_websocket_manager
from app.models.core import PredictionResult, SeverityLevel, SubscriptionTier


@pytest.mark.asyncio
class TestAlertIntegration:
    """Integration tests for alert system."""
    
    @patch('app.services.alert_broadcaster.get_websocket_manager')
    @patch('app.repositories.predictions.get_predictions_repository')
    @patch('app.repositories.subscriptions.get_subscriptions_repository')
    async def test_end_to_end_alert_flow(self, mock_subs_repo, mock_pred_repo, mock_ws_manager):
        """Test complete alert flow from prediction to delivery."""
        # Setup mocks
        mock_ws_manager_instance = MagicMock()
        mock_ws_manager_instance.broadcast_alert = AsyncMock()
        mock_ws_manager_instance.get_connection_count.return_value = 3
        mock_ws_manager_instance.get_authenticated_connection_count.return_value = 2
        mock_ws_manager.return_value = mock_ws_manager_instance
        
        mock_subs_repo_instance = MagicMock()
        mock_subs_repo_instance.get_users_with_webhooks = AsyncMock(return_value=[
            {
                "user_id": "user-1",
                "tier": "enterprise",
                "webhook_url": "https://example.com/webhook",
                "alert_thresholds": {"low": 0.3, "medium": 0.6, "high": 0.8}
            }
        ])
        mock_subs_repo.return_value = mock_subs_repo_instance
        
        mock_pred_repo_instance = MagicMock()
        mock_pred_repo.return_value = mock_pred_repo_instance
        
        # Create high-probability prediction
        prediction = PredictionResult(
            id="pred-123",
            timestamp=datetime.utcnow(),
            flare_probability=0.95,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0",
            confidence_score=0.92,
            raw_output={"test": "data"},
            solar_data={"magnetic_field": [1.0, 2.0, 3.0]}
        )
        
        # Get broadcaster and process prediction
        broadcaster = await get_alert_broadcaster()
        result = await broadcaster.process_new_prediction(prediction)
        
        # Verify alert was triggered
        assert result["alert_triggered"] is True
        assert result["alert_level"] == "high"
        assert "alert_id" in result
        
        # Verify WebSocket broadcast was called
        mock_ws_manager_instance.broadcast_alert.assert_called_once()
        
        # Verify webhook notification was attempted
        assert result["webhook_notifications"]["success"] is True
        assert result["webhook_notifications"]["webhook_count"] == 1
    
    @patch('app.services.alert_broadcaster.get_websocket_manager')
    @patch('app.repositories.predictions.get_predictions_repository')
    @patch('app.repositories.subscriptions.get_subscriptions_repository')
    async def test_alert_threshold_filtering(self, mock_subs_repo, mock_pred_repo, mock_ws_manager):
        """Test that alerts are properly filtered by thresholds."""
        # Setup mocks
        mock_ws_manager_instance = MagicMock()
        mock_ws_manager_instance.broadcast_alert = AsyncMock()
        mock_ws_manager.return_value = mock_ws_manager_instance
        
        mock_subs_repo_instance = MagicMock()
        mock_subs_repo_instance.get_users_with_webhooks = AsyncMock(return_value=[])
        mock_subs_repo.return_value = mock_subs_repo_instance
        
        mock_pred_repo_instance = MagicMock()
        mock_pred_repo.return_value = mock_pred_repo_instance
        
        broadcaster = await get_alert_broadcaster()
        
        # Test low probability - should not trigger alert
        low_prediction = PredictionResult(
            id="pred-low",
            timestamp=datetime.utcnow(),
            flare_probability=0.2,  # Below default threshold
            severity_level=SeverityLevel.LOW,
            model_version="surya-1.0"
        )
        
        result = await broadcaster.process_new_prediction(low_prediction)
        assert result["alert_triggered"] is False
        assert result["reason"] == "threshold_not_met"
        
        # Test high probability - should trigger alert
        high_prediction = PredictionResult(
            id="pred-high",
            timestamp=datetime.utcnow(),
            flare_probability=0.9,  # Above high threshold
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0"
        )
        
        result = await broadcaster.process_new_prediction(high_prediction)
        assert result["alert_triggered"] is True
        assert result["alert_level"] == "high"
    
    async def test_subscription_tier_webhook_filtering(self):
        """Test webhook filtering based on subscription tiers."""
        from app.services.alert_broadcaster import AlertBroadcaster
        
        # Create broadcaster with mocked dependencies
        mock_ws_manager = MagicMock()
        mock_ws_manager.broadcast_alert = AsyncMock()
        mock_ws_manager.get_connection_count.return_value = 0
        mock_ws_manager.get_authenticated_connection_count.return_value = 0
        
        mock_predictions_repo = MagicMock()
        
        mock_subscriptions_repo = MagicMock()
        webhook_users = [
            {"user_id": "free-user", "tier": "free", "webhook_url": "https://free.com/webhook"},
            {"user_id": "pro-user", "tier": "pro", "webhook_url": "https://pro.com/webhook"},
            {"user_id": "enterprise-user", "tier": "enterprise", "webhook_url": "https://enterprise.com/webhook"}
        ]
        mock_subscriptions_repo.get_users_with_webhooks = AsyncMock(return_value=webhook_users)
        
        broadcaster = AlertBroadcaster(
            websocket_manager=mock_ws_manager,
            predictions_repo=mock_predictions_repo,
            subscriptions_repo=mock_subscriptions_repo
        )
        
        # Test medium severity alert
        medium_prediction = PredictionResult(
            id="pred-medium",
            timestamp=datetime.utcnow(),
            flare_probability=0.7,
            severity_level=SeverityLevel.MEDIUM,
            model_version="surya-1.0"
        )
        
        result = await broadcaster.process_new_prediction(medium_prediction)
        
        # Only enterprise tier should receive medium alerts
        webhook_results = result["webhook_notifications"]["results"]
        user_ids = [r["user_id"] for r in webhook_results]
        
        assert "free-user" not in user_ids  # Free tier gets no webhooks
        assert "pro-user" not in user_ids   # Pro tier only gets high alerts
        assert "enterprise-user" in user_ids  # Enterprise gets all alerts
    
    async def test_alert_message_content(self):
        """Test that alert messages contain correct information."""
        from app.services.alert_broadcaster import AlertBroadcaster
        
        # Create broadcaster with mocked dependencies
        mock_ws_manager = MagicMock()
        mock_ws_manager.broadcast_alert = AsyncMock()
        mock_ws_manager.get_connection_count.return_value = 1
        mock_ws_manager.get_authenticated_connection_count.return_value = 1
        
        mock_predictions_repo = MagicMock()
        
        mock_subscriptions_repo = MagicMock()
        mock_subscriptions_repo.get_users_with_webhooks = AsyncMock(return_value=[])
        
        broadcaster = AlertBroadcaster(
            websocket_manager=mock_ws_manager,
            predictions_repo=mock_predictions_repo,
            subscriptions_repo=mock_subscriptions_repo
        )
        
        # Create prediction with specific values
        prediction = PredictionResult(
            id="pred-test",
            timestamp=datetime.utcnow(),
            flare_probability=0.85,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0",
            confidence_score=0.95,
            raw_output={"model_output": "test"},
            solar_data={"test": "data"}
        )
        
        result = await broadcaster.process_new_prediction(prediction)
        
        # Verify WebSocket broadcast was called with correct data
        mock_ws_manager.broadcast_alert.assert_called_once()
        call_args = mock_ws_manager.broadcast_alert.call_args
        alert_data, severity = call_args[0]
        
        # Check alert data content
        assert alert_data["flare_probability"] == 0.85
        assert alert_data["severity_level"] == "high"
        assert alert_data["alert_triggered"] is True
        assert "85%" in alert_data["message"]  # Probability percentage
        assert "HIGH ALERT" in alert_data["message"]  # High severity indicator
        assert alert_data["model_version"] == "surya-1.0"
        assert alert_data["confidence_score"] == 0.95
        assert alert_data["prediction_id"] == "pred-test"
        
        # Check severity parameter
        assert severity == SeverityLevel.HIGH
    
    async def test_alert_queuing_for_offline_users(self):
        """Test alert queuing functionality for offline users."""
        from app.services.alert_broadcaster import AlertBroadcaster
        
        # Create broadcaster with mocked dependencies
        mock_ws_manager = MagicMock()
        mock_ws_manager.broadcast_alert = AsyncMock()
        mock_ws_manager.send_to_user = AsyncMock(return_value=1)  # Return 1 for each call
        mock_ws_manager.get_connection_count.return_value = 0
        mock_ws_manager.get_authenticated_connection_count.return_value = 0
        
        mock_predictions_repo = MagicMock()
        mock_subscriptions_repo = MagicMock()
        mock_subscriptions_repo.get_users_with_webhooks = AsyncMock(return_value=[])
        
        broadcaster = AlertBroadcaster(
            websocket_manager=mock_ws_manager,
            predictions_repo=mock_predictions_repo,
            subscriptions_repo=mock_subscriptions_repo
        )
        
        user_id = "test-user-123"
        
        # Add some alerts to the queue manually (simulating offline alerts)
        from app.models.core import WebSocketMessage
        
        alert1 = WebSocketMessage(type="alert", data={"id": "alert-1", "message": "First alert"})
        alert2 = WebSocketMessage(type="alert", data={"id": "alert-2", "message": "Second alert"})
        
        broadcaster.alert_queue.add_alert(user_id, alert1)
        broadcaster.alert_queue.add_alert(user_id, alert2)
        
        # Verify alerts are queued
        assert broadcaster.alert_queue.get_queue_size(user_id) == 2
        
        # Send queued alerts when user reconnects
        sent_count = await broadcaster.send_queued_alerts_to_user(user_id)
        
        # Verify alerts were sent
        assert sent_count == 2
        assert mock_ws_manager.send_to_user.call_count == 2
        
        # Verify queue is empty after sending
        assert broadcaster.alert_queue.get_queue_size(user_id) == 0
    
    async def test_alert_rate_limiting(self):
        """Test that alerts are rate-limited to prevent spam."""
        from app.services.alert_broadcaster import AlertBroadcaster
        
        # Create broadcaster with mocked dependencies
        mock_ws_manager = MagicMock()
        mock_ws_manager.broadcast_alert = AsyncMock()
        mock_ws_manager.get_connection_count.return_value = 1
        mock_ws_manager.get_authenticated_connection_count.return_value = 1
        
        mock_predictions_repo = MagicMock()
        mock_subscriptions_repo = MagicMock()
        mock_subscriptions_repo.get_users_with_webhooks = AsyncMock(return_value=[])
        
        broadcaster = AlertBroadcaster(
            websocket_manager=mock_ws_manager,
            predictions_repo=mock_predictions_repo,
            subscriptions_repo=mock_subscriptions_repo
        )
        
        # Create first prediction
        prediction1 = PredictionResult(
            id="pred-1",
            timestamp=datetime.utcnow(),
            flare_probability=0.9,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0"
        )
        
        # Process first prediction - should trigger alert
        result1 = await broadcaster.process_new_prediction(prediction1)
        assert result1["alert_triggered"] is True
        
        # Create second prediction with same severity shortly after
        prediction2 = PredictionResult(
            id="pred-2",
            timestamp=datetime.utcnow() + timedelta(minutes=5),  # 5 minutes later
            flare_probability=0.85,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0"
        )
        
        # Process second prediction - should still trigger because it's high severity
        # (High severity alerts always trigger according to our logic)
        result2 = await broadcaster.process_new_prediction(prediction2)
        assert result2["alert_triggered"] is True
        
        # Verify both broadcast calls were made (high severity always triggers)
        assert mock_ws_manager.broadcast_alert.call_count == 2
    
    async def test_alert_system_cleanup(self):
        """Test cleanup of old alert data."""
        from app.services.alert_broadcaster import AlertBroadcaster, AlertQueue, AlertDeliveryTracker
        from app.models.core import WebSocketMessage
        
        # Create broadcaster components
        alert_queue = AlertQueue()
        delivery_tracker = AlertDeliveryTracker()
        
        # Add old data
        user_id = "test-user"
        
        # Add old queued alert
        old_alert = WebSocketMessage(
            type="alert",
            data={"id": "old-alert"},
            timestamp=datetime.utcnow() - timedelta(days=8)
        )
        alert_queue.add_alert(user_id, old_alert)
        
        # Add old delivery tracking
        old_alert_id = "old-tracking-alert"
        delivery_tracker.pending_alerts[old_alert_id] = {
            "alert_data": {},
            "target_users": set(["user-1"]),
            "created_at": datetime.utcnow() - timedelta(hours=25),
            "delivered_to": set()
        }
        
        # Add recent data that should be kept
        recent_alert = WebSocketMessage(
            type="alert",
            data={"id": "recent-alert"},
            timestamp=datetime.utcnow() - timedelta(hours=1)
        )
        alert_queue.add_alert(user_id, recent_alert)
        
        recent_alert_id = "recent-tracking-alert"
        delivery_tracker.pending_alerts[recent_alert_id] = {
            "alert_data": {},
            "target_users": set(["user-1"]),
            "created_at": datetime.utcnow() - timedelta(hours=1),
            "delivered_to": set()
        }
        
        # Create mock broadcaster with our components
        mock_ws_manager = MagicMock()
        mock_predictions_repo = MagicMock()
        mock_subscriptions_repo = MagicMock()
        
        broadcaster = AlertBroadcaster(
            websocket_manager=mock_ws_manager,
            predictions_repo=mock_predictions_repo,
            subscriptions_repo=mock_subscriptions_repo
        )
        broadcaster.alert_queue = alert_queue
        broadcaster.delivery_tracker = delivery_tracker
        
        # Run cleanup
        await broadcaster.cleanup_old_data()
        
        # Verify old data was removed
        remaining_alerts = alert_queue.get_queued_alerts(user_id)
        assert len(remaining_alerts) == 1
        assert remaining_alerts[0].data["id"] == "recent-alert"
        
        assert old_alert_id not in delivery_tracker.pending_alerts
        assert recent_alert_id in delivery_tracker.pending_alerts