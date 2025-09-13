"""WebSocket API endpoints for real-time alerts."""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.websocket_manager import get_websocket_manager, WebSocketManager
from app.services.auth_service import get_auth_service, AuthService, get_current_user
from app.models.core import WebSocketMessage
from app.middleware.subscription import require_websocket_access, get_api_key_subscription

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])
security = HTTPBearer(auto_error=False)


@router.websocket("/alerts")
async def websocket_alerts_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    WebSocket endpoint for real-time solar flare alerts.
    
    Query Parameters:
    - token: Optional JWT token for authentication
    
    Message Types (Client -> Server):
    - heartbeat: Keep connection alive
    - authenticate: Authenticate with JWT token
    - update_thresholds: Update alert thresholds
    
    Message Types (Server -> Client):
    - connection: Welcome message with connection info
    - alert: Solar flare alert notification
    - heartbeat: Server heartbeat
    - heartbeat_ack: Heartbeat acknowledgment
    - auth_success: Authentication successful
    - auth_error: Authentication failed
    - thresholds_updated: Alert thresholds updated
    - error: General error message
    """
    connection_id = None
    
    try:
        # Start background tasks if not already running
        await ws_manager.start_background_tasks()
        
        # Accept connection and authenticate if token provided
        connection_id = await ws_manager.connect(websocket, token)
        
        logger.info(f"WebSocket client connected: {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                await ws_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Send error message to client
                error_msg = WebSocketMessage(
                    type="error",
                    data={"message": "Error processing message"}
                )
                try:
                    await websocket.send_text(error_msg.model_dump_json())
                except:
                    break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up connection
        if connection_id:
            await ws_manager.disconnect(connection_id)


@router.get("/stats")
async def websocket_stats(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Get WebSocket connection statistics.
    Requires authentication for detailed stats.
    """
    # Basic stats available to everyone
    stats = {
        "total_connections": ws_manager.get_connection_count(),
        "authenticated_connections": ws_manager.get_authenticated_connection_count()
    }
    
    # Detailed stats for authenticated users
    if credentials and credentials.credentials:
        user_session = await auth_service.validate_token(credentials.credentials)
        if user_session:
            stats["user_connections"] = ws_manager.get_user_connection_count(user_session.user_id)
            stats["user_id"] = user_session.user_id
            stats["subscription_tier"] = user_session.subscription_tier
    
    return stats


@router.post("/broadcast")
async def broadcast_test_alert(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Broadcast a test alert to all connected clients.
    Requires authentication and admin privileges.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_session = await auth_service.validate_token(credentials.credentials)
    if not user_session:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # For now, allow any authenticated user to send test alerts
    # In production, this should be restricted to admin users
    
    from app.models.core import SeverityLevel
    from datetime import datetime
    
    test_alert_data = {
        "id": "test-alert-001",
        "timestamp": datetime.utcnow().isoformat(),
        "flare_probability": 0.85,
        "alert_triggered": True,
        "message": "Test alert: High probability solar flare detected",
        "test": True
    }
    
    await ws_manager.broadcast_alert(test_alert_data, SeverityLevel.HIGH)
    
    return {
        "success": True,
        "message": "Test alert broadcasted",
        "connections_notified": ws_manager.get_connection_count()
    }