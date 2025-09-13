"""Tests for WebSocket connection manager."""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.websocket_manager import WebSocketManager, ConnectionInfo
from app.services.auth_service import AuthService, UserSession
from app.models.core import WebSocketMessage, SeverityLevel, SubscriptionTier


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.messages_sent = []
        self.closed = False
        self.accept_called = False
    
    async def accept(self):
        self.accept_called = True
    
    async def send_text(self, message: str):
        if self.closed:
            raise Exception("WebSocket closed")
        self.messages_sent.append(message)
    
    async def receive_text(self):
        # This would be implemented by test cases
        raise NotImplementedError
    
    def close(self):
        self.closed = True


@pytest.fixture
def mock_auth_service():
    """Create mock authentication service."""
    auth_service = MagicMock(spec=AuthService)
    return auth_service


@pytest.fixture
def websocket_manager(mock_auth_service):
    """Create WebSocket manager with mock auth service."""
    return WebSocketManager(mock_auth_service)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    return MockWebSocket()


@pytest.fixture
def mock_user_session():
    """Create mock user session."""
    return UserSession(
        user_id="test-user-123",
        email="test@example.com",
        subscription_tier="pro",
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.mark.asyncio
class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    async def test_connect_without_token(self, websocket_manager, mock_websocket):
        """Test connecting without authentication token."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        assert mock_websocket.accept_called
        assert connection_id in websocket_manager.connections
        assert connection_id in websocket_manager.connection_info
        
        conn_info = websocket_manager.connection_info[connection_id]
        assert not conn_info.is_authenticated
        assert conn_info.user_id is None
        assert conn_info.subscription_tier == SubscriptionTier.FREE
        
        # Check welcome message was sent
        assert len(mock_websocket.messages_sent) == 1
        welcome_msg = json.loads(mock_websocket.messages_sent[0])
        assert welcome_msg["type"] == "connection"
        assert not welcome_msg["data"]["authenticated"]
    
    async def test_connect_with_valid_token(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test connecting with valid authentication token."""
        token = "valid-jwt-token"
        mock_auth_service.validate_token.return_value = mock_user_session
        
        connection_id = await websocket_manager.connect(mock_websocket, token)
        
        assert mock_websocket.accept_called
        mock_auth_service.validate_token.assert_called_once_with(token)
        
        conn_info = websocket_manager.connection_info[connection_id]
        assert conn_info.is_authenticated
        assert conn_info.user_id == mock_user_session.user_id
        assert conn_info.subscription_tier == SubscriptionTier.PRO
        
        # Check user is in user connections mapping
        assert mock_user_session.user_id in websocket_manager.user_connections
        assert connection_id in websocket_manager.user_connections[mock_user_session.user_id]
        
        # Check welcome message indicates authentication
        welcome_msg = json.loads(mock_websocket.messages_sent[0])
        assert welcome_msg["data"]["authenticated"]
        assert welcome_msg["data"]["subscription_tier"] == "pro"
    
    async def test_connect_with_invalid_token(self, websocket_manager, mock_websocket, mock_auth_service):
        """Test connecting with invalid authentication token."""
        token = "invalid-jwt-token"
        mock_auth_service.validate_token.return_value = None
        
        connection_id = await websocket_manager.connect(mock_websocket, token)
        
        conn_info = websocket_manager.connection_info[connection_id]
        assert not conn_info.is_authenticated
        assert conn_info.user_id is None
    
    async def test_disconnect(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test disconnecting a WebSocket connection."""
        # Connect first
        token = "valid-jwt-token"
        mock_auth_service.validate_token.return_value = mock_user_session
        connection_id = await websocket_manager.connect(mock_websocket, token)
        
        # Verify connection exists
        assert connection_id in websocket_manager.connections
        assert mock_user_session.user_id in websocket_manager.user_connections
        
        # Disconnect
        await websocket_manager.disconnect(connection_id)
        
        # Verify cleanup
        assert connection_id not in websocket_manager.connections
        assert connection_id not in websocket_manager.connection_info
        assert mock_user_session.user_id not in websocket_manager.user_connections
    
    async def test_authenticate_connection(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test authenticating an existing connection."""
        # Connect without token
        connection_id = await websocket_manager.connect(mock_websocket)
        assert not websocket_manager.connection_info[connection_id].is_authenticated
        
        # Authenticate
        token = "valid-jwt-token"
        mock_auth_service.validate_token.return_value = mock_user_session
        
        success = await websocket_manager.authenticate_connection(connection_id, token)
        
        assert success
        conn_info = websocket_manager.connection_info[connection_id]
        assert conn_info.is_authenticated
        assert conn_info.user_id == mock_user_session.user_id
        
        # Check auth success message was sent
        auth_msg = json.loads(mock_websocket.messages_sent[-1])
        assert auth_msg["type"] == "auth_success"
    
    async def test_authenticate_connection_invalid_token(self, websocket_manager, mock_websocket, mock_auth_service):
        """Test authenticating connection with invalid token."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        mock_auth_service.validate_token.return_value = None
        success = await websocket_manager.authenticate_connection(connection_id, "invalid-token")
        
        assert not success
        assert not websocket_manager.connection_info[connection_id].is_authenticated
    
    async def test_update_alert_thresholds(self, websocket_manager, mock_websocket):
        """Test updating alert thresholds for a connection."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        new_thresholds = {"low": 0.2, "medium": 0.5, "high": 0.9}
        success = await websocket_manager.update_alert_thresholds(connection_id, new_thresholds)
        
        assert success
        conn_info = websocket_manager.connection_info[connection_id]
        assert conn_info.alert_thresholds == new_thresholds
        
        # Check confirmation message was sent
        update_msg = json.loads(mock_websocket.messages_sent[-1])
        assert update_msg["type"] == "thresholds_updated"
    
    async def test_update_alert_thresholds_invalid(self, websocket_manager, mock_websocket):
        """Test updating alert thresholds with invalid values."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        # Missing required keys
        invalid_thresholds = {"low": 0.2, "medium": 0.5}
        success = await websocket_manager.update_alert_thresholds(connection_id, invalid_thresholds)
        assert not success
        
        # Invalid values (out of range)
        invalid_thresholds = {"low": -0.1, "medium": 0.5, "high": 1.5}
        success = await websocket_manager.update_alert_thresholds(connection_id, invalid_thresholds)
        assert not success
    
    async def test_broadcast_alert_free_tier(self, websocket_manager, mock_websocket):
        """Test broadcasting alerts to free tier users (high severity only)."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        alert_data = {
            "id": "test-alert",
            "timestamp": datetime.utcnow().isoformat(),
            "flare_probability": 0.9,
            "message": "High severity alert"
        }
        
        # Free tier should receive high severity alerts
        await websocket_manager.broadcast_alert(alert_data, SeverityLevel.HIGH)
        
        # Check alert was sent (welcome + alert messages)
        assert len(mock_websocket.messages_sent) == 2
        alert_msg = json.loads(mock_websocket.messages_sent[-1])
        assert alert_msg["type"] == "alert"
        assert alert_msg["data"]["severity"] == "high"
        
        # Free tier should NOT receive medium severity alerts
        mock_websocket.messages_sent.clear()
        await websocket_manager.broadcast_alert(alert_data, SeverityLevel.MEDIUM)
        
        # No new messages should be sent
        assert len(mock_websocket.messages_sent) == 0
    
    async def test_broadcast_alert_pro_tier(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test broadcasting alerts to pro tier users (all severities)."""
        # Connect with pro tier user
        mock_auth_service.validate_token.return_value = mock_user_session
        connection_id = await websocket_manager.connect(mock_websocket, "valid-token")
        
        alert_data = {
            "id": "test-alert",
            "timestamp": datetime.utcnow().isoformat(),
            "flare_probability": 0.7,
            "message": "Medium severity alert"
        }
        
        # Pro tier should receive medium severity alerts
        await websocket_manager.broadcast_alert(alert_data, SeverityLevel.MEDIUM)
        
        # Check alert was sent (welcome + alert messages)
        assert len(mock_websocket.messages_sent) == 2
        alert_msg = json.loads(mock_websocket.messages_sent[-1])
        assert alert_msg["type"] == "alert"
        assert alert_msg["data"]["severity"] == "medium"
    
    async def test_send_to_user(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test sending message to specific user."""
        # Connect user
        mock_auth_service.validate_token.return_value = mock_user_session
        connection_id = await websocket_manager.connect(mock_websocket, "valid-token")
        
        # Send message to user
        test_message = WebSocketMessage(
            type="test",
            data={"message": "Test message for user"}
        )
        
        sent_count = await websocket_manager.send_to_user(mock_user_session.user_id, test_message)
        
        assert sent_count == 1
        assert len(mock_websocket.messages_sent) == 2  # welcome + test message
        
        test_msg = json.loads(mock_websocket.messages_sent[-1])
        assert test_msg["type"] == "test"
        assert test_msg["data"]["message"] == "Test message for user"
    
    async def test_handle_heartbeat_message(self, websocket_manager, mock_websocket):
        """Test handling heartbeat message from client."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        # Record initial heartbeat time
        initial_heartbeat = websocket_manager.connection_info[connection_id].last_heartbeat
        
        # Wait a bit and send heartbeat
        await asyncio.sleep(0.1)
        heartbeat_msg = json.dumps({"type": "heartbeat"})
        await websocket_manager.handle_message(connection_id, heartbeat_msg)
        
        # Check heartbeat was updated
        updated_heartbeat = websocket_manager.connection_info[connection_id].last_heartbeat
        assert updated_heartbeat > initial_heartbeat
        
        # Check heartbeat acknowledgment was sent
        ack_msg = json.loads(mock_websocket.messages_sent[-1])
        assert ack_msg["type"] == "heartbeat_ack"
    
    async def test_handle_authenticate_message(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test handling authenticate message from client."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        # Send authenticate message
        mock_auth_service.validate_token.return_value = mock_user_session
        auth_msg = json.dumps({"type": "authenticate", "token": "valid-token"})
        await websocket_manager.handle_message(connection_id, auth_msg)
        
        # Check connection is now authenticated
        conn_info = websocket_manager.connection_info[connection_id]
        assert conn_info.is_authenticated
        assert conn_info.user_id == mock_user_session.user_id
    
    async def test_handle_update_thresholds_message(self, websocket_manager, mock_websocket):
        """Test handling update thresholds message from client."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        # Send update thresholds message
        thresholds_msg = json.dumps({
            "type": "update_thresholds",
            "thresholds": {"low": 0.1, "medium": 0.4, "high": 0.7}
        })
        await websocket_manager.handle_message(connection_id, thresholds_msg)
        
        # Check thresholds were updated
        conn_info = websocket_manager.connection_info[connection_id]
        assert conn_info.alert_thresholds["low"] == 0.1
        assert conn_info.alert_thresholds["medium"] == 0.4
        assert conn_info.alert_thresholds["high"] == 0.7
    
    async def test_handle_invalid_json_message(self, websocket_manager, mock_websocket):
        """Test handling invalid JSON message from client."""
        connection_id = await websocket_manager.connect(mock_websocket)
        
        # Send invalid JSON
        await websocket_manager.handle_message(connection_id, "invalid json {")
        
        # Should not crash, just log error
        # Connection should still be active
        assert connection_id in websocket_manager.connections
    
    async def test_connection_counts(self, websocket_manager, mock_websocket, mock_auth_service, mock_user_session):
        """Test connection counting methods."""
        # Initially no connections
        assert websocket_manager.get_connection_count() == 0
        assert websocket_manager.get_authenticated_connection_count() == 0
        
        # Add unauthenticated connection
        connection_id1 = await websocket_manager.connect(MockWebSocket())
        assert websocket_manager.get_connection_count() == 1
        assert websocket_manager.get_authenticated_connection_count() == 0
        
        # Add authenticated connection
        mock_auth_service.validate_token.return_value = mock_user_session
        connection_id2 = await websocket_manager.connect(MockWebSocket(), "valid-token")
        assert websocket_manager.get_connection_count() == 2
        assert websocket_manager.get_authenticated_connection_count() == 1
        assert websocket_manager.get_user_connection_count(mock_user_session.user_id) == 1
    
    async def test_should_receive_alert_logic(self, websocket_manager):
        """Test alert filtering logic based on subscription and thresholds."""
        # Free tier connection
        free_conn_info = ConnectionInfo(
            connection_id="free-conn",
            subscription_tier=SubscriptionTier.FREE,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            alert_thresholds={"low": 0.3, "medium": 0.6, "high": 0.8}
        )
        
        # Pro tier connection
        pro_conn_info = ConnectionInfo(
            connection_id="pro-conn",
            subscription_tier=SubscriptionTier.PRO,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            alert_thresholds={"low": 0.3, "medium": 0.6, "high": 0.8}
        )
        
        # Test free tier - only high severity
        assert not websocket_manager._should_receive_alert(free_conn_info, 0.7, SeverityLevel.MEDIUM)
        assert websocket_manager._should_receive_alert(free_conn_info, 0.9, SeverityLevel.HIGH)
        
        # Test pro tier - all severities if above threshold
        assert websocket_manager._should_receive_alert(pro_conn_info, 0.7, SeverityLevel.MEDIUM)
        assert websocket_manager._should_receive_alert(pro_conn_info, 0.9, SeverityLevel.HIGH)
        assert not websocket_manager._should_receive_alert(pro_conn_info, 0.5, SeverityLevel.MEDIUM)  # Below threshold