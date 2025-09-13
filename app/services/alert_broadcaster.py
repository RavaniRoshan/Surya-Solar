"""Alert broadcasting system for real-time notifications."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from uuid import uuid4
import json

from app.models.core import (
    PredictionResult, SeverityLevel, SubscriptionTier, 
    WebSocketMessage, AlertResponse
)
from app.services.websocket_manager import WebSocketManager, get_websocket_manager
from app.repositories.predictions import PredictionsRepository
from app.repositories.subscriptions import SubscriptionsRepository

logger = logging.getLogger(__name__)


class AlertThresholdEvaluator:
    """Evaluates alert thresholds and determines when to trigger alerts."""
    
    def __init__(self):
        self.default_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8
        }
    
    def evaluate_alert_level(self, probability: float, thresholds: Optional[Dict[str, float]] = None) -> Optional[SeverityLevel]:
        """
        Evaluate the alert level based on probability and thresholds.
        
        Args:
            probability: Solar flare probability (0.0 to 1.0)
            thresholds: Custom thresholds or None to use defaults
            
        Returns:
            SeverityLevel if alert should be triggered, None otherwise
        """
        if thresholds is None:
            thresholds = self.default_thresholds
        
        # Check thresholds in descending order of severity
        if probability >= thresholds.get("high", 0.8):
            return SeverityLevel.HIGH
        elif probability >= thresholds.get("medium", 0.6):
            return SeverityLevel.MEDIUM
        elif probability >= thresholds.get("low", 0.3):
            return SeverityLevel.LOW
        
        return None
    
    def should_trigger_alert(self, current_prediction: PredictionResult, 
                           previous_prediction: Optional[PredictionResult] = None,
                           thresholds: Optional[Dict[str, float]] = None) -> bool:
        """
        Determine if an alert should be triggered based on current and previous predictions.
        
        Args:
            current_prediction: Current prediction result
            previous_prediction: Previous prediction result for comparison
            thresholds: Custom alert thresholds
            
        Returns:
            True if alert should be triggered, False otherwise
        """
        current_level = self.evaluate_alert_level(current_prediction.flare_probability, thresholds)
        
        # No alert if probability doesn't meet any threshold
        if current_level is None:
            return False
        
        # Always trigger for high severity
        if current_level == SeverityLevel.HIGH:
            return True
        
        # For medium/low severity, only trigger if it's an increase from previous
        if previous_prediction is None:
            return True
        
        previous_level = self.evaluate_alert_level(previous_prediction.flare_probability, thresholds)
        
        # Trigger if severity level increased or if it's been more than 1 hour since last alert
        if previous_level is None or current_level.value != previous_level.value:
            return True
        
        # Check time-based re-alerting (every hour for persistent high alerts)
        time_diff = current_prediction.timestamp - previous_prediction.timestamp
        if current_level == SeverityLevel.HIGH and time_diff >= timedelta(hours=1):
            return True
        
        return False


class AlertQueue:
    """Queue system for managing alerts to offline clients."""
    
    def __init__(self, max_queue_size: int = 100):
        self.queues: Dict[str, List[WebSocketMessage]] = {}  # user_id -> messages
        self.max_queue_size = max_queue_size
    
    def add_alert(self, user_id: str, alert_message: WebSocketMessage):
        """Add alert to user's queue."""
        if user_id not in self.queues:
            self.queues[user_id] = []
        
        queue = self.queues[user_id]
        queue.append(alert_message)
        
        # Maintain queue size limit
        if len(queue) > self.max_queue_size:
            queue.pop(0)  # Remove oldest message
        
        logger.debug(f"Added alert to queue for user {user_id}. Queue size: {len(queue)}")
    
    def get_queued_alerts(self, user_id: str) -> List[WebSocketMessage]:
        """Get and clear queued alerts for a user."""
        if user_id not in self.queues:
            return []
        
        alerts = self.queues[user_id].copy()
        self.queues[user_id].clear()
        
        logger.debug(f"Retrieved {len(alerts)} queued alerts for user {user_id}")
        return alerts
    
    def clear_user_queue(self, user_id: str):
        """Clear all queued alerts for a user."""
        if user_id in self.queues:
            del self.queues[user_id]
    
    def get_queue_size(self, user_id: str) -> int:
        """Get the number of queued alerts for a user."""
        return len(self.queues.get(user_id, []))


class AlertDeliveryTracker:
    """Tracks alert delivery status and confirmations."""
    
    def __init__(self):
        self.pending_alerts: Dict[str, Dict[str, Any]] = {}  # alert_id -> alert_info
        self.delivery_confirmations: Dict[str, Set[str]] = {}  # alert_id -> set of user_ids
    
    def track_alert(self, alert_id: str, alert_data: Dict[str, Any], target_users: List[str]):
        """Start tracking an alert delivery."""
        self.pending_alerts[alert_id] = {
            "alert_data": alert_data,
            "target_users": set(target_users),
            "created_at": datetime.utcnow(),
            "delivered_to": set()
        }
        self.delivery_confirmations[alert_id] = set()
        
        logger.info(f"Started tracking alert {alert_id} for {len(target_users)} users")
    
    def confirm_delivery(self, alert_id: str, user_id: str):
        """Confirm alert delivery to a specific user."""
        if alert_id in self.pending_alerts:
            self.pending_alerts[alert_id]["delivered_to"].add(user_id)
            self.delivery_confirmations[alert_id].add(user_id)
            
            logger.debug(f"Confirmed delivery of alert {alert_id} to user {user_id}")
    
    def get_delivery_status(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status for an alert."""
        if alert_id not in self.pending_alerts:
            return None
        
        alert_info = self.pending_alerts[alert_id]
        delivered_count = len(alert_info["delivered_to"])
        target_count = len(alert_info["target_users"])
        
        return {
            "alert_id": alert_id,
            "target_users": target_count,
            "delivered_users": delivered_count,
            "delivery_rate": delivered_count / target_count if target_count > 0 else 0,
            "pending_users": alert_info["target_users"] - alert_info["delivered_to"],
            "created_at": alert_info["created_at"]
        }
    
    def cleanup_old_alerts(self, max_age_hours: int = 24):
        """Clean up old alert tracking data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        alerts_to_remove = []
        for alert_id, alert_info in self.pending_alerts.items():
            if alert_info["created_at"] < cutoff_time:
                alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.pending_alerts[alert_id]
            if alert_id in self.delivery_confirmations:
                del self.delivery_confirmations[alert_id]
        
        if alerts_to_remove:
            logger.info(f"Cleaned up {len(alerts_to_remove)} old alert tracking records")


class AlertBroadcaster:
    """Main alert broadcasting system."""
    
    def __init__(self, 
                 websocket_manager: WebSocketManager,
                 predictions_repo: PredictionsRepository,
                 subscriptions_repo: SubscriptionsRepository):
        self.ws_manager = websocket_manager
        self.predictions_repo = predictions_repo
        self.subscriptions_repo = subscriptions_repo
        self.threshold_evaluator = AlertThresholdEvaluator()
        self.alert_queue = AlertQueue()
        self.delivery_tracker = AlertDeliveryTracker()
        self._last_prediction: Optional[PredictionResult] = None
    
    async def process_new_prediction(self, prediction: PredictionResult) -> Dict[str, Any]:
        """
        Process a new prediction and broadcast alerts if necessary.
        
        Args:
            prediction: New prediction result
            
        Returns:
            Dictionary with broadcast results
        """
        try:
            # Evaluate if alert should be triggered
            should_alert = self.threshold_evaluator.should_trigger_alert(
                prediction, self._last_prediction
            )
            
            if not should_alert:
                logger.debug(f"No alert triggered for prediction {prediction.id}")
                return {"alert_triggered": False, "reason": "threshold_not_met"}
            
            # Determine alert severity
            alert_level = self.threshold_evaluator.evaluate_alert_level(prediction.flare_probability)
            if alert_level is None:
                return {"alert_triggered": False, "reason": "no_severity_level"}
            
            # Create alert data
            alert_data = await self._create_alert_data(prediction, alert_level)
            
            # Broadcast to WebSocket connections
            ws_results = await self._broadcast_to_websockets(alert_data, alert_level)
            
            # Send webhook notifications
            webhook_results = await self._send_webhook_notifications(alert_data, alert_level)
            
            # Store alert in history
            await self._store_alert_history(prediction, alert_level, alert_data)
            
            # Update last prediction
            self._last_prediction = prediction
            
            results = {
                "alert_triggered": True,
                "alert_level": alert_level.value,
                "alert_id": alert_data["id"],
                "websocket_broadcast": ws_results,
                "webhook_notifications": webhook_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Alert broadcast completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing prediction for alerts: {e}", exc_info=True)
            return {"alert_triggered": False, "error": str(e)}
    
    async def _create_alert_data(self, prediction: PredictionResult, alert_level: SeverityLevel) -> Dict[str, Any]:
        """Create alert data structure."""
        alert_id = str(uuid4())
        
        # Create human-readable message
        probability_percent = int(prediction.flare_probability * 100)
        severity_messages = {
            SeverityLevel.LOW: f"Low solar flare risk detected ({probability_percent}% probability)",
            SeverityLevel.MEDIUM: f"Moderate solar flare risk detected ({probability_percent}% probability)",
            SeverityLevel.HIGH: f"HIGH ALERT: High solar flare risk detected ({probability_percent}% probability)"
        }
        
        return {
            "id": alert_id,
            "timestamp": prediction.timestamp.isoformat(),
            "flare_probability": prediction.flare_probability,
            "severity_level": alert_level.value,
            "alert_triggered": True,
            "message": severity_messages[alert_level],
            "model_version": prediction.model_version,
            "confidence_score": prediction.confidence_score,
            "prediction_id": prediction.id
        }
    
    async def _broadcast_to_websockets(self, alert_data: Dict[str, Any], alert_level: SeverityLevel) -> Dict[str, Any]:
        """Broadcast alert to WebSocket connections."""
        try:
            # Create WebSocket message
            ws_message = WebSocketMessage(
                type="alert",
                data=alert_data
            )
            
            # Broadcast to all eligible connections
            await self.ws_manager.broadcast_alert(alert_data, alert_level)
            
            # Get connection counts for reporting
            total_connections = self.ws_manager.get_connection_count()
            auth_connections = self.ws_manager.get_authenticated_connection_count()
            
            return {
                "success": True,
                "total_connections": total_connections,
                "authenticated_connections": auth_connections,
                "message_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error broadcasting to WebSockets: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_webhook_notifications(self, alert_data: Dict[str, Any], alert_level: SeverityLevel) -> Dict[str, Any]:
        """Send webhook notifications to subscribed users."""
        try:
            # Get users with webhook URLs configured
            webhook_users = await self.subscriptions_repo.get_users_with_webhooks()
            
            if not webhook_users:
                return {"success": True, "webhook_count": 0, "message": "No webhook subscribers"}
            
            # Filter users based on subscription tier and alert level
            eligible_users = []
            for user in webhook_users:
                if self._user_should_receive_webhook(user, alert_level):
                    eligible_users.append(user)
            
            # Send webhooks (implement actual HTTP calls in production)
            webhook_results = []
            for user in eligible_users:
                try:
                    # In a real implementation, this would make HTTP POST requests
                    # For now, we'll just log and simulate success
                    logger.info(f"Would send webhook to {user['webhook_url']} for user {user['user_id']}")
                    webhook_results.append({
                        "user_id": user["user_id"],
                        "webhook_url": user["webhook_url"],
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Failed to send webhook to user {user['user_id']}: {e}")
                    webhook_results.append({
                        "user_id": user["user_id"],
                        "webhook_url": user["webhook_url"],
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "webhook_count": len(webhook_results),
                "results": webhook_results
            }
            
        except Exception as e:
            logger.error(f"Error sending webhook notifications: {e}")
            return {"success": False, "error": str(e)}
    
    def _user_should_receive_webhook(self, user: Dict[str, Any], alert_level: SeverityLevel) -> bool:
        """Determine if user should receive webhook for this alert level."""
        user_tier = SubscriptionTier(user.get("tier", "free"))
        
        # Free tier: no webhooks
        if user_tier == SubscriptionTier.FREE:
            return False
        
        # Pro tier: high alerts only
        if user_tier == SubscriptionTier.PRO and alert_level != SeverityLevel.HIGH:
            return False
        
        # Enterprise tier: all alerts
        return True
    
    async def _store_alert_history(self, prediction: PredictionResult, alert_level: SeverityLevel, alert_data: Dict[str, Any]):
        """Store alert in history for tracking and analytics."""
        try:
            # Create alert response record
            alert_response = AlertResponse(
                id=alert_data["id"],
                timestamp=prediction.timestamp,
                flare_probability=prediction.flare_probability,
                severity_level=alert_level,
                alert_triggered=True,
                message=alert_data["message"]
            )
            
            # Store in database (implement in predictions repository)
            # For now, just log
            logger.info(f"Stored alert history: {alert_response.id}")
            
        except Exception as e:
            logger.error(f"Error storing alert history: {e}")
    
    async def send_queued_alerts_to_user(self, user_id: str) -> int:
        """Send queued alerts to a user when they reconnect."""
        try:
            queued_alerts = self.alert_queue.get_queued_alerts(user_id)
            
            if not queued_alerts:
                return 0
            
            # Send each queued alert
            sent_count = 0
            for alert in queued_alerts:
                sent = await self.ws_manager.send_to_user(user_id, alert)
                sent_count += sent
            
            logger.info(f"Sent {sent_count} queued alerts to user {user_id}")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending queued alerts to user {user_id}: {e}")
            return 0
    
    async def get_alert_delivery_stats(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery statistics for a specific alert."""
        return self.delivery_tracker.get_delivery_status(alert_id)
    
    async def cleanup_old_data(self):
        """Clean up old tracking data and queues."""
        try:
            # Clean up old delivery tracking
            self.delivery_tracker.cleanup_old_alerts()
            
            # Clean up old queued alerts (older than 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            for user_id, queue in list(self.alert_queue.queues.items()):
                # Remove old messages from queue
                self.alert_queue.queues[user_id] = [
                    msg for msg in queue 
                    if msg.timestamp > cutoff_time
                ]
                
                # Remove empty queues
                if not self.alert_queue.queues[user_id]:
                    del self.alert_queue.queues[user_id]
            
            logger.info("Completed alert system cleanup")
            
        except Exception as e:
            logger.error(f"Error during alert system cleanup: {e}")


# Global alert broadcaster instance
_alert_broadcaster: Optional[AlertBroadcaster] = None


async def get_alert_broadcaster() -> AlertBroadcaster:
    """Get the global alert broadcaster instance."""
    global _alert_broadcaster
    if _alert_broadcaster is None:
        # Initialize dependencies
        ws_manager = get_websocket_manager()
        
        from app.repositories.predictions import get_predictions_repository
        from app.repositories.subscriptions import get_subscriptions_repository
        
        predictions_repo = get_predictions_repository()
        subscriptions_repo = get_subscriptions_repository()
        
        _alert_broadcaster = AlertBroadcaster(
            websocket_manager=ws_manager,
            predictions_repo=predictions_repo,
            subscriptions_repo=subscriptions_repo
        )
    
    return _alert_broadcaster