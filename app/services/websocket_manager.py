"""WebSocket connection manager for real-time alerts."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List, Any
from uuid import uuid4
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.models.core import WebSocketMessage, SeverityLevel, SubscriptionTier
from app.services.auth_service import AuthService, UserSession

logger = logging.getLogger(__name__)


class ConnectionInfo(BaseModel):
    """Information about a WebSocket connection."""
    connection_id: str
    user_id: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    connected_at: datetime
    last_heartbeat: datetime
    alert_thresholds: Dict[str, float] = {"low": 0.3, "medium": 0.6, "high": 0.8}
    is_authenticated: bool = False


class WebSocketManager:
    """Manages WebSocket connections for real-time alerts."""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 300  # 5 minutes
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start_background_tasks(self):
        """Start background tasks for heartbeat and cleanup."""
        if not self._heartbeat_task or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_background_tasks(self):
        """Stop background tasks."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> str:
        """
        Accept a new WebSocket connection and authenticate if token provided.
        
        Args:
            websocket: FastAPI WebSocket instance
            token: Optional JWT token for authentication
            
        Returns:
            Connection ID for the new connection
        """
        await websocket.accept()
        
        connection_id = str(uuid4())
        now = datetime.utcnow()
        
        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            connected_at=now,
            last_heartbeat=now
        )
        
        # Authenticate if token provided
        if token:
            user_session = await self.auth_service.validate_token(token)
            if user_session:
                conn_info.user_id = user_session.user_id
                conn_info.subscription_tier = SubscriptionTier(user_session.subscription_tier)
                conn_info.is_authenticated = True
                
                # Add to user connections mapping
                if user_session.user_id not in self.user_connections:
                    self.user_connections[user_session.user_id] = set()
                self.user_connections[user_session.user_id].add(connection_id)
                
                logger.info(f"Authenticated WebSocket connection: {connection_id} for user: {user_session.user_id}")
            else:
                logger.warning(f"Invalid token provided for WebSocket connection: {connection_id}")
        
        # Store connection
        self.connections[connection_id] = websocket
        self.connection_info[connection_id] = conn_info
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type="connection",
            data={
                "connection_id": connection_id,
                "authenticated": conn_info.is_authenticated,
                "subscription_tier": conn_info.subscription_tier.value,
                "message": "Connected to ZERO-COMP real-time alerts"
            }
        )
        
        await self._send_message(connection_id, welcome_msg)
        
        logger.info(f"New WebSocket connection: {connection_id} (authenticated: {conn_info.is_authenticated})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect and clean up a WebSocket connection.
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        if connection_id in self.connections:
            conn_info = self.connection_info.get(connection_id)
            
            # Remove from user connections mapping
            if conn_info and conn_info.user_id:
                user_connections = self.user_connections.get(conn_info.user_id, set())
                user_connections.discard(connection_id)
                if not user_connections:
                    del self.user_connections[conn_info.user_id]
            
            # Clean up connection
            del self.connections[connection_id]
            if connection_id in self.connection_info:
                del self.connection_info[connection_id]
            
            logger.info(f"WebSocket connection disconnected: {connection_id}")
    
    async def authenticate_connection(self, connection_id: str, token: str) -> bool:
        """
        Authenticate an existing connection with a token.
        
        Args:
            connection_id: ID of the connection to authenticate
            token: JWT token for authentication
            
        Returns:
            True if authentication successful, False otherwise
        """
        if connection_id not in self.connection_info:
            return False
        
        user_session = await self.auth_service.validate_token(token)
        if not user_session:
            return False
        
        conn_info = self.connection_info[connection_id]
        conn_info.user_id = user_session.user_id
        conn_info.subscription_tier = SubscriptionTier(user_session.subscription_tier)
        conn_info.is_authenticated = True
        
        # Add to user connections mapping
        if user_session.user_id not in self.user_connections:
            self.user_connections[user_session.user_id] = set()
        self.user_connections[user_session.user_id].add(connection_id)
        
        # Send authentication success message
        auth_msg = WebSocketMessage(
            type="auth_success",
            data={
                "user_id": user_session.user_id,
                "subscription_tier": conn_info.subscription_tier.value,
                "message": "Authentication successful"
            }
        )
        
        await self._send_message(connection_id, auth_msg)
        
        logger.info(f"WebSocket connection authenticated: {connection_id} for user: {user_session.user_id}")
        return True
    
    async def update_alert_thresholds(self, connection_id: str, thresholds: Dict[str, float]) -> bool:
        """
        Update alert thresholds for a connection.
        
        Args:
            connection_id: ID of the connection
            thresholds: New alert thresholds
            
        Returns:
            True if update successful, False otherwise
        """
        if connection_id not in self.connection_info:
            return False
        
        # Validate thresholds
        required_keys = {"low", "medium", "high"}
        if not all(key in thresholds for key in required_keys):
            return False
        
        if not all(0.0 <= value <= 1.0 for value in thresholds.values()):
            return False
        
        self.connection_info[connection_id].alert_thresholds = thresholds
        
        # Send confirmation
        update_msg = WebSocketMessage(
            type="thresholds_updated",
            data={
                "thresholds": thresholds,
                "message": "Alert thresholds updated successfully"
            }
        )
        
        await self._send_message(connection_id, update_msg)
        return True
    
    async def broadcast_alert(self, alert_data: Dict[str, Any], severity: SeverityLevel):
        """
        Broadcast alert to all eligible connections based on their thresholds and subscription tiers.
        
        Args:
            alert_data: Alert data to broadcast
            severity: Alert severity level
        """
        if not self.connections:
            return
        
        flare_probability = alert_data.get("flare_probability", 0.0)
        
        # Create alert message
        alert_msg = WebSocketMessage(
            type="alert",
            data={
                **alert_data,
                "severity": severity.value,
                "alert_type": "solar_flare"
            }
        )
        
        broadcast_count = 0
        
        for connection_id, conn_info in self.connection_info.items():
            # Check if connection should receive this alert
            if self._should_receive_alert(conn_info, flare_probability, severity):
                success = await self._send_message(connection_id, alert_msg)
                if success:
                    broadcast_count += 1
        
        logger.info(f"Broadcasted alert to {broadcast_count} connections (severity: {severity.value})")
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """
        Send message to all connections for a specific user.
        
        Args:
            user_id: User ID to send message to
            message: Message to send
            
        Returns:
            Number of connections the message was sent to
        """
        user_connection_ids = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for connection_id in user_connection_ids.copy():  # Copy to avoid modification during iteration
            success = await self._send_message(connection_id, message)
            if success:
                sent_count += 1
        
        return sent_count
    
    async def handle_message(self, connection_id: str, message: str):
        """
        Handle incoming message from WebSocket client.
        
        Args:
            connection_id: ID of the connection that sent the message
            message: Raw message string
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "heartbeat":
                await self._handle_heartbeat(connection_id)
            elif msg_type == "authenticate":
                token = data.get("token")
                if token:
                    success = await self.authenticate_connection(connection_id, token)
                    if not success:
                        error_msg = WebSocketMessage(
                            type="auth_error",
                            data={"message": "Authentication failed"}
                        )
                        await self._send_message(connection_id, error_msg)
            elif msg_type == "update_thresholds":
                thresholds = data.get("thresholds", {})
                success = await self.update_alert_thresholds(connection_id, thresholds)
                if not success:
                    error_msg = WebSocketMessage(
                        type="error",
                        data={"message": "Failed to update alert thresholds"}
                    )
                    await self._send_message(connection_id, error_msg)
            else:
                logger.warning(f"Unknown message type from {connection_id}: {msg_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from {connection_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connections)
    
    def get_authenticated_connection_count(self) -> int:
        """Get number of authenticated connections."""
        return sum(1 for info in self.connection_info.values() if info.is_authenticated)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user."""
        return len(self.user_connections.get(user_id, set()))
    
    async def _send_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """
        Send message to a specific connection.
        
        Args:
            connection_id: ID of the connection
            message: Message to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if connection_id not in self.connections:
            return False
        
        try:
            websocket = self.connections[connection_id]
            await websocket.send_text(message.model_dump_json())
            return True
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def _handle_heartbeat(self, connection_id: str):
        """Handle heartbeat message from client."""
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_heartbeat = datetime.utcnow()
            
            # Send heartbeat response
            heartbeat_msg = WebSocketMessage(
                type="heartbeat_ack",
                data={"message": "Heartbeat acknowledged"}
            )
            await self._send_message(connection_id, heartbeat_msg)
    
    def _should_receive_alert(self, conn_info: ConnectionInfo, probability: float, severity: SeverityLevel) -> bool:
        """
        Determine if a connection should receive an alert based on thresholds and subscription.
        
        Args:
            conn_info: Connection information
            probability: Flare probability
            severity: Alert severity
            
        Returns:
            True if connection should receive alert, False otherwise
        """
        # Check subscription tier limits
        if conn_info.subscription_tier == SubscriptionTier.FREE:
            # Free tier only gets high severity alerts
            if severity != SeverityLevel.HIGH:
                return False
        
        # Check alert thresholds
        threshold_key = severity.value
        threshold = conn_info.alert_thresholds.get(threshold_key, 0.8)
        
        return probability >= threshold
    
    async def _heartbeat_loop(self):
        """Background task to send periodic heartbeats."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if not self.connections:
                    continue
                
                heartbeat_msg = WebSocketMessage(
                    type="heartbeat",
                    data={"message": "Server heartbeat"}
                )
                
                # Send heartbeat to all connections
                for connection_id in list(self.connections.keys()):
                    await self._send_message(connection_id, heartbeat_msg)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _cleanup_loop(self):
        """Background task to clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                stale_connections = []
                
                for connection_id, conn_info in self.connection_info.items():
                    time_since_heartbeat = (now - conn_info.last_heartbeat).total_seconds()
                    if time_since_heartbeat > self.connection_timeout:
                        stale_connections.append(connection_id)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    logger.info(f"Disconnecting stale connection: {connection_id}")
                    await self.disconnect(connection_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        from app.services.auth_service import get_auth_service
        _websocket_manager = WebSocketManager(get_auth_service())
    return _websocket_manager