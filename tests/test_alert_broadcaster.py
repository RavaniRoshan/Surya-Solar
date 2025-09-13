"""Tests for alert broadcasting system."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.alert_broadcaster import (
    AlertThresholdEvaluator, AlertQueue, AlertDeliveryTracker, AlertBroadcaster
)
from app.models.core import (
    PredictionResult, SeverityLevel, SubscriptionTier, WebSocketMessage
)


@pytest.fixture
def threshold_evaluator():
    """Create alert threshold evaluator."""
    return AlertThresholdEvaluator()


@pytest.fixture
def alert_queue():
    """Create alert queue."""
    return AlertQueue()


@pytest.fixture
def delivery_tracker():
    """Create alert delivery tracker."""
    return AlertDeliveryTracker()


@pytest.fixture
def mock_websocket_manager():
    """Create mock WebSocket manager."""
    manager = MagicMock()
    manager.broadcast_alert = AsyncMock()
    manager.send_to_user = AsyncMock(return_value=1)
    manager.get_connection_count.return_value = 5
    manager.get_authenticated_connection_count.return_value = 3
    return manager


@pytest.fixture
def mock_predictions_repo():
    """Create mock predictions repository."""
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_subscriptions_repo():
    """Create mock subscriptions repository."""
    repo = MagicMock()
    repo.get_users_with_webhooks = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def sample_prediction():
    """Create sample prediction result."""
    return PredictionResult(
        id="pred-123",
        timestamp=datetime.utcnow(),
        flare_probability=0.85,
        severity_level=SeverityLevel.HIGH,
        model_version="surya-1.0",
        confidence_score=0.92,
        raw_output={"test": "data"},
        solar_data={"magnetic_field": [1.0, 2.0, 3.0]}
    )


@pytest.fixture
def alert_broadcaster(mock_websocket_manager, mock_predictions_repo, mock_subscriptions_repo):
    """Create alert broadcaster with mocked dependencies."""
    return AlertBroadcaster(
        websocket_manager=mock_websocket_manager,
        predictions_repo=mock_predictions_repo,
        subscriptions_repo=mock_subscriptions_repo
    )


class TestAlertThresholdEvaluator:
    """Test alert threshold evaluation logic."""
    
    def test_evaluate_alert_level_default_thresholds(self, threshold_evaluator):
        """Test alert level evaluation with default thresholds."""
        # Test high severity
        assert threshold_evaluator.evaluate_alert_level(0.9) == SeverityLevel.HIGH
        assert threshold_evaluator.evaluate_alert_level(0.8) == SeverityLevel.HIGH
        
        # Test medium severity
        assert threshold_evaluator.evaluate_alert_level(0.7) == SeverityLevel.MEDIUM
        assert threshold_evaluator.evaluate_alert_level(0.6) == SeverityLevel.MEDIUM
        
        # Test low severity
        assert threshold_evaluator.evaluate_alert_level(0.5) == SeverityLevel.LOW
        assert threshold_evaluator.evaluate_alert_level(0.3) == SeverityLevel.LOW
        
        # Test no alert
        assert threshold_evaluator.evaluate_alert_level(0.2) is None
        assert threshold_evaluator.evaluate_alert_level(0.0) is None
    
    def test_evaluate_alert_level_custom_thresholds(self, threshold_evaluator):
        """Test alert level evaluation with custom thresholds."""
        custom_thresholds = {"low": 0.2, "medium": 0.5, "high": 0.9}
        
        # Test with custom thresholds
        assert threshold_evaluator.evaluate_alert_level(0.95, custom_thresholds) == SeverityLevel.HIGH
        assert threshold_evaluator.evaluate_alert_level(0.7, custom_thresholds) == SeverityLevel.MEDIUM
        assert threshold_evaluator.evaluate_alert_level(0.3, custom_thresholds) == SeverityLevel.LOW
        assert threshold_evaluator.evaluate_alert_level(0.1, custom_thresholds) is None
    
    def test_should_trigger_alert_first_prediction(self, threshold_evaluator, sample_prediction):
        """Test alert triggering for first prediction."""
        # High probability should trigger
        sample_prediction.flare_probability = 0.9
        assert threshold_evaluator.should_trigger_alert(sample_prediction) is True
        
        # Low probability should not trigger
        sample_prediction.flare_probability = 0.1
        assert threshold_evaluator.should_trigger_alert(sample_prediction) is False
    
    def test_should_trigger_alert_with_previous(self, threshold_evaluator, sample_prediction):
        """Test alert triggering with previous prediction."""
        # Create previous prediction
        previous_prediction = PredictionResult(
            id="pred-122",
            timestamp=datetime.utcnow() - timedelta(minutes=10),
            flare_probability=0.4,
            severity_level=SeverityLevel.LOW,
            model_version="surya-1.0"
        )
        
        # Increased severity should trigger
        sample_prediction.flare_probability = 0.9
        assert threshold_evaluator.should_trigger_alert(sample_prediction, previous_prediction) is True
        
        # Same severity should not trigger (unless high)
        sample_prediction.flare_probability = 0.5
        previous_prediction.flare_probability = 0.4
        assert threshold_evaluator.should_trigger_alert(sample_prediction, previous_prediction) is False
        
        # High severity should always trigger
        sample_prediction.flare_probability = 0.9
        previous_prediction.flare_probability = 0.85
        assert threshold_evaluator.should_trigger_alert(sample_prediction, previous_prediction) is True
    
    def test_should_trigger_alert_time_based(self, threshold_evaluator, sample_prediction):
        """Test time-based alert re-triggering."""
        # Create old previous prediction (more than 1 hour ago)
        previous_prediction = PredictionResult(
            id="pred-122",
            timestamp=datetime.utcnow() - timedelta(hours=2),
            flare_probability=0.9,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0"
        )
        
        # High severity should re-trigger after 1 hour
        sample_prediction.flare_probability = 0.9
        assert threshold_evaluator.should_trigger_alert(sample_prediction, previous_prediction) is True


class TestAlertQueue:
    """Test alert queue functionality."""
    
    def test_add_and_get_alerts(self, alert_queue):
        """Test adding and retrieving alerts from queue."""
        user_id = "user-123"
        
        # Add alerts to queue
        alert1 = WebSocketMessage(type="alert", data={"id": "alert-1"})
        alert2 = WebSocketMessage(type="alert", data={"id": "alert-2"})
        
        alert_queue.add_alert(user_id, alert1)
        alert_queue.add_alert(user_id, alert2)
        
        # Check queue size
        assert alert_queue.get_queue_size(user_id) == 2
        
        # Get queued alerts (should clear queue)
        queued = alert_queue.get_queued_alerts(user_id)
        assert len(queued) == 2
        assert queued[0].data["id"] == "alert-1"
        assert queued[1].data["id"] == "alert-2"
        
        # Queue should be empty after retrieval
        assert alert_queue.get_queue_size(user_id) == 0
    
    def test_queue_size_limit(self, alert_queue):
        """Test queue size limit enforcement."""
        user_id = "user-123"
        alert_queue.max_queue_size = 3
        
        # Add more alerts than limit
        for i in range(5):
            alert = WebSocketMessage(type="alert", data={"id": f"alert-{i}"})
            alert_queue.add_alert(user_id, alert)
        
        # Should only keep the last 3 alerts
        assert alert_queue.get_queue_size(user_id) == 3
        
        queued = alert_queue.get_queued_alerts(user_id)
        assert len(queued) == 3
        assert queued[0].data["id"] == "alert-2"  # Oldest kept
        assert queued[2].data["id"] == "alert-4"  # Newest
    
    def test_clear_user_queue(self, alert_queue):
        """Test clearing user queue."""
        user_id = "user-123"
        
        # Add alerts
        alert = WebSocketMessage(type="alert", data={"id": "alert-1"})
        alert_queue.add_alert(user_id, alert)
        
        assert alert_queue.get_queue_size(user_id) == 1
        
        # Clear queue
        alert_queue.clear_user_queue(user_id)
        assert alert_queue.get_queue_size(user_id) == 0


class TestAlertDeliveryTracker:
    """Test alert delivery tracking."""
    
    def test_track_and_confirm_delivery(self, delivery_tracker):
        """Test tracking alert delivery."""
        alert_id = "alert-123"
        alert_data = {"message": "Test alert"}
        target_users = ["user-1", "user-2", "user-3"]
        
        # Start tracking
        delivery_tracker.track_alert(alert_id, alert_data, target_users)
        
        # Confirm deliveries
        delivery_tracker.confirm_delivery(alert_id, "user-1")
        delivery_tracker.confirm_delivery(alert_id, "user-2")
        
        # Check status
        status = delivery_tracker.get_delivery_status(alert_id)
        assert status is not None
        assert status["target_users"] == 3
        assert status["delivered_users"] == 2
        assert status["delivery_rate"] == 2/3
        assert "user-3" in status["pending_users"]
    
    def test_cleanup_old_alerts(self, delivery_tracker):
        """Test cleanup of old alert tracking data."""
        # Add old alert
        old_alert_id = "old-alert"
        delivery_tracker.pending_alerts[old_alert_id] = {
            "alert_data": {},
            "target_users": set(["user-1"]),
            "created_at": datetime.utcnow() - timedelta(hours=25),
            "delivered_to": set()
        }
        
        # Add recent alert
        recent_alert_id = "recent-alert"
        delivery_tracker.pending_alerts[recent_alert_id] = {
            "alert_data": {},
            "target_users": set(["user-1"]),
            "created_at": datetime.utcnow() - timedelta(hours=1),
            "delivered_to": set()
        }
        
        # Cleanup (max age 24 hours)
        delivery_tracker.cleanup_old_alerts(24)
        
        # Old alert should be removed, recent should remain
        assert old_alert_id not in delivery_tracker.pending_alerts
        assert recent_alert_id in delivery_tracker.pending_alerts


@pytest.mark.asyncio
class TestAlertBroadcaster:
    """Test alert broadcaster functionality."""
    
    async def test_process_new_prediction_no_alert(self, alert_broadcaster, sample_prediction):
        """Test processing prediction that doesn't trigger alert."""
        # Low probability prediction
        sample_prediction.flare_probability = 0.1
        
        result = await alert_broadcaster.process_new_prediction(sample_prediction)
        
        assert result["alert_triggered"] is False
        assert result["reason"] == "threshold_not_met"
    
    async def test_process_new_prediction_with_alert(self, alert_broadcaster, sample_prediction, mock_websocket_manager, mock_subscriptions_repo):
        """Test processing prediction that triggers alert."""
        # High probability prediction
        sample_prediction.flare_probability = 0.9
        
        # Mock webhook users
        mock_subscriptions_repo.get_users_with_webhooks.return_value = [
            {"user_id": "user-1", "tier": "enterprise", "webhook_url": "https://example.com/webhook"}
        ]
        
        result = await alert_broadcaster.process_new_prediction(sample_prediction)
        
        assert result["alert_triggered"] is True
        assert result["alert_level"] == "high"
        assert "alert_id" in result
        
        # Verify WebSocket broadcast was called
        mock_websocket_manager.broadcast_alert.assert_called_once()
    
    async def test_broadcast_to_websockets(self, alert_broadcaster, mock_websocket_manager):
        """Test WebSocket broadcasting."""
        alert_data = {
            "id": "alert-123",
            "message": "Test alert",
            "flare_probability": 0.9
        }
        
        result = await alert_broadcaster._broadcast_to_websockets(alert_data, SeverityLevel.HIGH)
        
        assert result["success"] is True
        assert result["total_connections"] == 5
        assert result["authenticated_connections"] == 3
        
        # Verify broadcast was called
        mock_websocket_manager.broadcast_alert.assert_called_once_with(alert_data, SeverityLevel.HIGH)
    
    async def test_send_webhook_notifications_no_users(self, alert_broadcaster, mock_subscriptions_repo):
        """Test webhook notifications with no subscribed users."""
        mock_subscriptions_repo.get_users_with_webhooks.return_value = []
        
        alert_data = {"id": "alert-123", "message": "Test alert"}
        result = await alert_broadcaster._send_webhook_notifications(alert_data, SeverityLevel.HIGH)
        
        assert result["success"] is True
        assert result["webhook_count"] == 0
    
    async def test_send_webhook_notifications_with_users(self, alert_broadcaster, mock_subscriptions_repo):
        """Test webhook notifications with subscribed users."""
        webhook_users = [
            {"user_id": "user-1", "tier": "pro", "webhook_url": "https://example1.com/webhook"},
            {"user_id": "user-2", "tier": "enterprise", "webhook_url": "https://example2.com/webhook"},
            {"user_id": "user-3", "tier": "free", "webhook_url": "https://example3.com/webhook"}  # Should be filtered out
        ]
        mock_subscriptions_repo.get_users_with_webhooks.return_value = webhook_users
        
        alert_data = {"id": "alert-123", "message": "Test alert"}
        result = await alert_broadcaster._send_webhook_notifications(alert_data, SeverityLevel.HIGH)
        
        assert result["success"] is True
        assert result["webhook_count"] == 2  # Free tier user filtered out for high alerts
        
        # Check that pro and enterprise users are included
        user_ids = [r["user_id"] for r in result["results"]]
        assert "user-1" in user_ids  # Pro tier gets high alerts
        assert "user-2" in user_ids  # Enterprise tier gets all alerts
    
    def test_user_should_receive_webhook_tier_filtering(self, alert_broadcaster):
        """Test webhook filtering based on subscription tier."""
        free_user = {"tier": "free"}
        pro_user = {"tier": "pro"}
        enterprise_user = {"tier": "enterprise"}
        
        # Free tier: no webhooks
        assert not alert_broadcaster._user_should_receive_webhook(free_user, SeverityLevel.HIGH)
        assert not alert_broadcaster._user_should_receive_webhook(free_user, SeverityLevel.MEDIUM)
        assert not alert_broadcaster._user_should_receive_webhook(free_user, SeverityLevel.LOW)
        
        # Pro tier: high alerts only
        assert alert_broadcaster._user_should_receive_webhook(pro_user, SeverityLevel.HIGH)
        assert not alert_broadcaster._user_should_receive_webhook(pro_user, SeverityLevel.MEDIUM)
        assert not alert_broadcaster._user_should_receive_webhook(pro_user, SeverityLevel.LOW)
        
        # Enterprise tier: all alerts
        assert alert_broadcaster._user_should_receive_webhook(enterprise_user, SeverityLevel.HIGH)
        assert alert_broadcaster._user_should_receive_webhook(enterprise_user, SeverityLevel.MEDIUM)
        assert alert_broadcaster._user_should_receive_webhook(enterprise_user, SeverityLevel.LOW)
    
    async def test_send_queued_alerts_to_user(self, alert_broadcaster, mock_websocket_manager):
        """Test sending queued alerts to reconnected user."""
        user_id = "user-123"
        
        # Add alerts to queue
        alert1 = WebSocketMessage(type="alert", data={"id": "alert-1"})
        alert2 = WebSocketMessage(type="alert", data={"id": "alert-2"})
        
        alert_broadcaster.alert_queue.add_alert(user_id, alert1)
        alert_broadcaster.alert_queue.add_alert(user_id, alert2)
        
        # Send queued alerts
        sent_count = await alert_broadcaster.send_queued_alerts_to_user(user_id)
        
        assert sent_count == 2
        assert mock_websocket_manager.send_to_user.call_count == 2
        
        # Queue should be empty after sending
        assert alert_broadcaster.alert_queue.get_queue_size(user_id) == 0
    
    async def test_cleanup_old_data(self, alert_broadcaster):
        """Test cleanup of old tracking data."""
        # Add old queued alert
        user_id = "user-123"
        old_alert = WebSocketMessage(
            type="alert", 
            data={"id": "old-alert"},
            timestamp=datetime.utcnow() - timedelta(days=8)
        )
        recent_alert = WebSocketMessage(
            type="alert", 
            data={"id": "recent-alert"},
            timestamp=datetime.utcnow() - timedelta(hours=1)
        )
        
        alert_broadcaster.alert_queue.add_alert(user_id, old_alert)
        alert_broadcaster.alert_queue.add_alert(user_id, recent_alert)
        
        # Run cleanup
        await alert_broadcaster.cleanup_old_data()
        
        # Old alert should be removed, recent should remain
        remaining_alerts = alert_broadcaster.alert_queue.get_queued_alerts(user_id)
        assert len(remaining_alerts) == 1
        assert remaining_alerts[0].data["id"] == "recent-alert"
    
    async def test_create_alert_data(self, alert_broadcaster, sample_prediction):
        """Test alert data creation."""
        alert_data = await alert_broadcaster._create_alert_data(sample_prediction, SeverityLevel.HIGH)
        
        assert "id" in alert_data
        assert alert_data["flare_probability"] == sample_prediction.flare_probability
        assert alert_data["severity_level"] == "high"
        assert alert_data["alert_triggered"] is True
        assert "HIGH ALERT" in alert_data["message"]
        assert alert_data["prediction_id"] == sample_prediction.id
    
    async def test_error_handling(self, alert_broadcaster, sample_prediction, mock_websocket_manager):
        """Test error handling in alert processing."""
        # Make WebSocket broadcast fail
        mock_websocket_manager.broadcast_alert.side_effect = Exception("WebSocket error")
        
        sample_prediction.flare_probability = 0.9
        result = await alert_broadcaster.process_new_prediction(sample_prediction)
        
        # Should still return success for the overall process
        assert result["alert_triggered"] is True
        assert "websocket_broadcast" in result
        assert result["websocket_broadcast"]["success"] is False