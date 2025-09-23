# WebSocket Real-time Alerts

Connect to ZERO-COMP's WebSocket endpoint for real-time solar flare notifications.

## Connection

**Endpoint:** `wss://api.zero-comp.com/ws/alerts`

**Authentication:** Include JWT token as query parameter:
```
wss://api.zero-comp.com/ws/alerts?token=your-jwt-token
```

**Requirements:** Pro or Enterprise subscription

## Message Types

### Server → Client Messages

#### Connection Confirmation
```json
{
  "type": "connection",
  "data": {
    "connection_id": "conn_abc123",
    "authenticated": true,
    "subscription_tier": "pro",
    "message": "Connected successfully"
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Solar Flare Alert
```json
{
  "type": "alert",
  "data": {
    "id": "alert_1705327800",
    "timestamp": "2024-01-15T14:30:00Z",
    "flare_probability": 0.85,
    "severity_level": "high",
    "alert_triggered": true,
    "message": "High severity solar flare prediction: 85.0% probability"
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Heartbeat
```json
{
  "type": "heartbeat",
  "data": {"status": "alive"},
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Error
```json
{
  "type": "error",
  "data": {
    "error_code": "AUTHENTICATION_FAILED",
    "message": "Invalid or expired token"
  },
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### Client → Server Messages

#### Heartbeat Response
```json
{
  "type": "heartbeat_ack",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### Update Alert Thresholds
```json
{
  "type": "update_thresholds",
  "data": {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8
  }
}
```

## Implementation Examples

### JavaScript (Browser)
```javascript
class SolarAlertClient {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect() {
    this.ws = new WebSocket(`wss://api.zero-comp.com/ws/alerts?token=${this.token}`);
    
    this.ws.onopen = () => {
      console.log('Connected to solar weather alerts');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
    
    this.ws.onclose = () => {
      console.log('Connection closed');
      this.reconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  handleMessage(message) {
    switch (message.type) {
      case 'alert':
        this.onAlert(message.data);
        break;
      case 'heartbeat':
        this.sendHeartbeatAck();
        break;
      case 'error':
        console.error('Server error:', message.data);
        break;
    }
  }
  
  onAlert(alertData) {
    if (alertData.alert_triggered) {
      // Show browser notification
      if (Notification.permission === 'granted') {
        new Notification('Solar Flare Alert', {
          body: `${alertData.severity_level.toUpperCase()}: ${(alertData.flare_probability * 100).toFixed(1)}% probability`,
          icon: '/solar-icon.png'
        });
      }
      
      // Custom alert handling
      console.log('🚨 Solar flare alert:', alertData);
    }
  }
  
  sendHeartbeatAck() {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'heartbeat_ack',
        timestamp: new Date().toISOString()
      }));
    }
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    }
  }
  
  updateThresholds(thresholds) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'update_thresholds',
        data: thresholds
      }));
    }
  }
}

// Usage
const client = new SolarAlertClient('your-jwt-token');
client.connect();
```

### Python (asyncio)
```python
import asyncio
import websockets
import json

class SolarAlertClient:
    def __init__(self, token):
        self.token = token
        self.uri = f"wss://api.zero-comp.com/ws/alerts?token={token}"
    
    async def connect(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                print("Connected to solar weather alerts")
                
                async for message in websocket:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                    
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        except Exception as e:
            print(f"Error: {e}")
    
    async def handle_message(self, websocket, message):
        if message["type"] == "alert":
            await self.on_alert(message["data"])
        elif message["type"] == "heartbeat":
            await self.send_heartbeat_ack(websocket)
        elif message["type"] == "error":
            print(f"Server error: {message['data']}")
    
    async def on_alert(self, alert_data):
        if alert_data["alert_triggered"]:
            print(f"🚨 Solar flare alert: {alert_data['flare_probability']:.1%} probability")
            print(f"Severity: {alert_data['severity_level']}")
            
            # Custom alert handling (send email, trigger systems, etc.)
            await self.handle_high_solar_activity(alert_data)
    
    async def send_heartbeat_ack(self, websocket):
        await websocket.send(json.dumps({
            "type": "heartbeat_ack",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }))
    
    async def handle_high_solar_activity(self, alert_data):
        # Implement your custom logic here
        # e.g., send notifications, trigger protective measures
        pass

# Usage
async def main():
    client = SolarAlertClient("your-jwt-token")
    await client.connect()

asyncio.run(main())
```

## Connection Management

### Heartbeat System
- Server sends heartbeat every 30 seconds
- Client should respond with `heartbeat_ack`
- Connection closed if no response within 60 seconds

### Reconnection Strategy
- Implement exponential backoff for reconnections
- Maximum 5 reconnection attempts recommended
- Check token validity if repeated connection failures

### Error Handling
- Handle network disconnections gracefully
- Validate message format before processing
- Log errors for debugging

## Rate Limits

WebSocket connections have the following limits:

| Tier | Max Connections | Message Rate |
|------|----------------|--------------|
| Pro | 5 concurrent | 10 messages/minute |
| Enterprise | 25 concurrent | 100 messages/minute |

## Best Practices

1. **Implement reconnection logic** with exponential backoff
2. **Handle heartbeats** to maintain connection
3. **Validate message format** before processing
4. **Store alerts locally** for offline access
5. **Rate limit your responses** to avoid overwhelming your systems
