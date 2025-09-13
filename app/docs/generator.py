"""API documentation generator for ZERO-COMP Solar Weather API."""

import json
import os
from typing import Dict, Any, List
from pathlib import Path

from app.docs.openapi_customization import add_code_examples


class APIDocumentationGenerator:
    """Generate comprehensive API documentation from OpenAPI schema."""
    
    def __init__(self, output_dir: str = "docs/api"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.code_examples = add_code_examples()
    
    def generate_documentation(self, openapi_schema: Dict[str, Any]) -> None:
        """Generate complete API documentation from OpenAPI schema."""
        
        # Generate main API reference
        self._generate_api_reference(openapi_schema)
        
        # Generate authentication guide
        self._generate_auth_guide()
        
        # Generate getting started guide
        self._generate_getting_started()
        
        # Generate WebSocket documentation
        self._generate_websocket_docs()
        
        # Generate error handling guide
        self._generate_error_guide()
        
        print(f"✅ API documentation generated in {self.output_dir}")
    
    def _generate_api_reference(self, schema: Dict[str, Any]) -> None:
        """Generate comprehensive API reference documentation."""
        
        content = f"""# ZERO-COMP Solar Weather API Reference

{schema.get('info', {}).get('description', '')}

## Base URL
```
https://api.zero-comp.com
```

## Authentication
All API endpoints require authentication using either:
- JWT tokens (for dashboard users)  
- API keys (for programmatic access)

Include the token in the Authorization header:
```
Authorization: Bearer <your-token-or-api-key>
```

## Endpoints

"""
        
        # Process each endpoint
        paths = schema.get('paths', {})
        for path, methods in paths.items():
            content += f"\n### {path}\n\n"
            
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                    content += self._format_endpoint_docs(path, method.upper(), details)
        
        self._write_file("api-reference.md", content) 
   
    def _format_endpoint_docs(self, path: str, method: str, details: Dict[str, Any]) -> str:
        """Format documentation for a single endpoint."""
        
        content = f"#### {method} {path}\n\n"
        
        # Add summary and description
        if 'summary' in details:
            content += f"**{details['summary']}**\n\n"
        
        if 'description' in details:
            content += f"{details['description']}\n\n"
        
        # Add parameters
        if 'parameters' in details:
            content += "**Parameters:**\n\n"
            for param in details['parameters']:
                required = " (required)" if param.get('required', False) else ""
                content += f"- `{param['name']}`{required}: {param.get('description', '')}\n"
            content += "\n"
        
        # Add request body
        if 'requestBody' in details:
            content += "**Request Body:**\n\n"
            content += "```json\n"
            # Add example request body if available
            content += "{\n  // Request body schema\n}\n"
            content += "```\n\n"
        
        # Add responses
        if 'responses' in details:
            content += "**Responses:**\n\n"
            for status_code, response in details['responses'].items():
                content += f"- `{status_code}`: {response.get('description', '')}\n"
            content += "\n"
        
        return content
    
    def _generate_auth_guide(self) -> None:
        """Generate authentication documentation."""
        
        content = """# Authentication Guide

ZERO-COMP API supports two authentication methods:

## 1. JWT Tokens (Dashboard Users)

JWT tokens are obtained through the web dashboard login process:

1. Sign up/login at [https://dashboard.zero-comp.com](https://dashboard.zero-comp.com)
2. The dashboard automatically handles JWT token management
3. Tokens are valid for 24 hours and automatically refreshed

### Using JWT Tokens

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \\
     https://api.zero-comp.com/api/v1/alerts/current
```

## 2. API Keys (Programmatic Access)

API keys provide programmatic access for Pro and Enterprise subscribers:

### Generating API Keys

1. Login to the dashboard
2. Navigate to Account Settings → API Keys
3. Click "Generate New API Key"
4. **Important**: Copy the key immediately - it won't be shown again

### Using API Keys

```bash
curl -H "Authorization: Bearer zc_your-api-key-here" \\
     https://api.zero-comp.com/api/v1/alerts/current
```

### API Key Format

API keys follow the format: `zc_` followed by 32 random characters.

Example: `zc_abc123def456ghi789jkl012mno345pqr678`

## Security Best Practices

1. **Never expose API keys in client-side code**
2. **Store API keys securely** (environment variables, secure vaults)
3. **Rotate API keys regularly** (every 90 days recommended)
4. **Use HTTPS only** - never send credentials over HTTP
5. **Monitor API usage** for suspicious activity

## Rate Limiting

Authentication affects rate limits:

| Tier | Rate Limit |
|------|------------|
| Free | 10 requests/hour |
| Pro | 1,000 requests/hour |
| Enterprise | 10,000 requests/hour |

## Troubleshooting

### Common Authentication Errors

**401 Unauthorized**
- Invalid or expired token
- Missing Authorization header
- Malformed token format

**403 Forbidden**  
- Valid token but insufficient permissions
- Feature requires higher subscription tier

**429 Rate Limit Exceeded**
- Too many requests for your tier
- Check `X-RateLimit-Reset` header for retry time
"""
        
        self._write_file("authentication.md", content)
    
    def _generate_getting_started(self) -> None:
        """Generate getting started guide."""
        
        content = """# Getting Started with ZERO-COMP API

This guide will help you make your first API call and integrate solar weather alerts into your application.

## Quick Start

### 1. Sign Up and Get API Access

1. **Create Account**: Sign up at [https://dashboard.zero-comp.com](https://dashboard.zero-comp.com)
2. **Choose Plan**: Select Free (dashboard only), Pro ($50/month), or Enterprise ($500/month)
3. **Generate API Key**: Pro/Enterprise users can generate API keys for programmatic access

### 2. Make Your First API Call

```bash
# Get current solar flare probability
curl -H "Authorization: Bearer your-api-key" \\
     https://api.zero-comp.com/api/v1/alerts/current
```

**Response:**
```json
{
  "current_probability": 0.75,
  "severity_level": "high", 
  "last_updated": "2024-01-15T14:30:00Z",
  "next_update": "2024-01-15T14:40:00Z",
  "alert_active": true
}
```

### 3. Get Historical Data

```bash
# Get last 24 hours of predictions
curl -H "Authorization: Bearer your-api-key" \\
     "https://api.zero-comp.com/api/v1/alerts/history?hours_back=24"
```

### 4. Set Up Real-time Alerts

For real-time notifications, use WebSocket connections:

```javascript
const ws = new WebSocket('wss://api.zero-comp.com/ws/alerts?token=your-jwt-token');

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  if (alert.type === 'alert' && alert.data.alert_triggered) {
    console.log(`🚨 Solar flare alert: ${alert.data.flare_probability * 100}% probability`);
  }
};
```

## Common Use Cases

### Satellite Operations

Monitor solar weather to protect satellite systems:

```python
import requests
import time

def check_satellite_safety():
    response = requests.get(
        "https://api.zero-comp.com/api/v1/alerts/current",
        headers={"Authorization": "Bearer your-api-key"}
    )
    
    alert = response.json()
    
    if alert['alert_active'] and alert['severity_level'] == 'high':
        print("⚠️  HIGH SOLAR ACTIVITY - Consider satellite protection mode")
        return False  # Not safe for sensitive operations
    
    return True  # Safe to operate

# Check every 10 minutes
while True:
    safe = check_satellite_safety()
    time.sleep(600)  # 10 minutes
```

### Power Grid Management

Plan maintenance windows during low solar activity:

```python
def find_maintenance_window(hours_ahead=48):
    response = requests.get(
        f"https://api.zero-comp.com/api/v1/alerts/history?hours_back={hours_ahead}",
        headers={"Authorization": "Bearer your-api-key"}
    )
    
    alerts = response.json()['alerts']
    
    # Find periods with low solar activity
    safe_periods = []
    for alert in alerts:
        if alert['flare_probability'] < 0.3:  # Low probability
            safe_periods.append(alert['timestamp'])
    
    return safe_periods
```

### Aviation Route Planning

Adjust polar routes based on solar weather:

```python
def check_polar_route_safety(route_coords):
    response = requests.get(
        "https://api.zero-comp.com/api/v1/alerts/current",
        headers={"Authorization": "Bearer your-api-key"}
    )
    
    alert = response.json()
    
    # High solar activity affects polar routes more
    if alert['severity_level'] in ['medium', 'high']:
        return {
            'safe': False,
            'recommendation': 'Use alternative non-polar route',
            'probability': alert['current_probability']
        }
    
    return {'safe': True, 'probability': alert['current_probability']}
```

## Next Steps

1. **Explore the API**: Try different endpoints and parameters
2. **Set Up Webhooks**: Configure webhook URLs for automated notifications
3. **Monitor Usage**: Check your API usage in the dashboard
4. **Join Community**: Get support and share use cases

## Support

- **Documentation**: [https://docs.zero-comp.com](https://docs.zero-comp.com)
- **Support Email**: support@zero-comp.com
- **Status Page**: [https://status.zero-comp.com](https://status.zero-comp.com)
"""
        
        self._write_file("getting-started.md", content)    

    def _generate_websocket_docs(self) -> None:
        """Generate WebSocket documentation."""
        
        content = """# WebSocket Real-time Alerts

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
"""
        
        self._write_file("websockets.md", content)
    
    def _generate_error_guide(self) -> None:
        """Generate error handling documentation."""
        
        content = """# Error Handling Guide

ZERO-COMP API uses standard HTTP status codes and provides detailed error information to help you handle issues gracefully.

## Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for your subscription tier",
  "details": {
    "limit": 10,
    "window": "1 hour",
    "retry_after": 3600
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

## HTTP Status Codes

### 2xx Success
- **200 OK**: Request successful
- **201 Created**: Resource created successfully

### 4xx Client Errors

#### 400 Bad Request
Invalid request parameters or malformed request body.

**Common Causes:**
- Invalid parameter values
- Missing required fields
- Malformed JSON

**Example:**
```json
{
  "error_code": "INVALID_PARAMETERS",
  "message": "Invalid request parameters",
  "details": {
    "field": "hours_back",
    "error": "must be between 1 and 168"
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

#### 401 Unauthorized
Authentication required or invalid credentials.

**Common Causes:**
- Missing Authorization header
- Invalid or expired JWT token
- Invalid API key format

**Example:**
```json
{
  "error_code": "AUTHENTICATION_REQUIRED",
  "message": "Valid authentication credentials required",
  "details": {
    "hint": "Include 'Authorization: Bearer <token>' header"
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

#### 403 Forbidden
Valid authentication but insufficient permissions.

**Common Causes:**
- Feature requires higher subscription tier
- API key lacks required permissions
- Account suspended

**Example:**
```json
{
  "error_code": "INSUFFICIENT_SUBSCRIPTION",
  "message": "This feature requires Pro or Enterprise subscription",
  "details": {
    "current_tier": "free",
    "required_tier": "pro",
    "upgrade_url": "https://dashboard.zero-comp.com/upgrade"
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

#### 404 Not Found
Requested resource does not exist.

**Example:**
```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "No current prediction available",
  "details": {
    "resource": "current_prediction",
    "hint": "Predictions are generated every 10 minutes"
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

#### 429 Rate Limit Exceeded
Too many requests for your subscription tier.

**Response Headers:**
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

**Example:**
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for your subscription tier",
  "details": {
    "limit": 10,
    "window": "1 hour",
    "retry_after": 3600,
    "current_tier": "free"
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

### 5xx Server Errors

#### 500 Internal Server Error
Unexpected server error.

**Example:**
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred",
  "details": {},
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

#### 503 Service Unavailable
Service temporarily unavailable (maintenance, overload).

**Example:**
```json
{
  "error_code": "SERVICE_UNAVAILABLE",
  "message": "Service temporarily unavailable",
  "details": {
    "reason": "scheduled_maintenance",
    "estimated_duration": "30 minutes"
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req_abc123def456"
}
```

## Error Handling Best Practices

### 1. Implement Retry Logic

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def get_current_alert_with_retry():
    session = create_session_with_retries()
    
    try:
        response = session.get(
            "https://api.zero-comp.com/api/v1/alerts/current",
            headers={"Authorization": "Bearer your-api-key"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            # Handle rate limiting
            retry_after = int(e.response.headers.get('X-RateLimit-Reset', 3600))
            print(f"Rate limited. Retry after {retry_after} seconds")
            time.sleep(retry_after)
            return get_current_alert_with_retry()
        else:
            print(f"HTTP error: {e.response.status_code}")
            print(f"Error details: {e.response.json()}")
            raise
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise
```

### 2. Handle Rate Limits Gracefully

```python
def handle_rate_limit(response):
    if response.status_code == 429:
        error_data = response.json()
        retry_after = error_data.get('details', {}).get('retry_after', 3600)
        
        print(f"Rate limit exceeded. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return True  # Indicate retry needed
    
    return False  # No retry needed

def api_call_with_rate_limit_handling(url, headers):
    while True:
        response = requests.get(url, headers=headers)
        
        if not handle_rate_limit(response):
            break
    
    return response
```

### 3. Validate Responses

```python
def validate_alert_response(data):
    required_fields = ['current_probability', 'severity_level', 'last_updated']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate probability range
    prob = data['current_probability']
    if not 0.0 <= prob <= 1.0:
        raise ValueError(f"Invalid probability value: {prob}")
    
    # Validate severity level
    valid_levels = ['low', 'medium', 'high']
    if data['severity_level'] not in valid_levels:
        raise ValueError(f"Invalid severity level: {data['severity_level']}")
    
    return True

def get_validated_alert():
    response = requests.get(
        "https://api.zero-comp.com/api/v1/alerts/current",
        headers={"Authorization": "Bearer your-api-key"}
    )
    
    if response.status_code == 200:
        data = response.json()
        validate_alert_response(data)
        return data
    else:
        error_data = response.json()
        raise Exception(f"API error: {error_data['message']}")
```

### 4. Log Errors for Debugging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def api_call_with_logging(url, headers):
    try:
        logger.info(f"Making API call to {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logger.info("API call successful")
            return response.json()
        else:
            error_data = response.json()
            logger.error(f"API error {response.status_code}: {error_data['message']}")
            logger.error(f"Request ID: {error_data.get('request_id')}")
            raise Exception(f"API error: {error_data['message']}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        raise
```

## WebSocket Error Handling

### Connection Errors

```javascript
class RobustWebSocketClient {
  constructor(url, token) {
    this.url = url;
    this.token = token;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
  }
  
  connect() {
    try {
      this.ws = new WebSocket(`${this.url}?token=${this.token}`);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000; // Reset delay
      };
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (e) {
          console.error('Invalid message format:', event.data);
        }
      };
      
      this.ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
        this.handleReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.handleReconnect();
    }
  }
  
  handleMessage(message) {
    if (message.type === 'error') {
      console.error('Server error:', message.data);
      
      if (message.data.error_code === 'AUTHENTICATION_FAILED') {
        console.error('Authentication failed - check your token');
        // Don't reconnect on auth failures
        return;
      }
    }
    
    // Handle other message types...
  }
  
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    console.log(`Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
    
    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
  }
}
```

## Support and Debugging

When reporting issues, include:

1. **Request ID** from error response
2. **Timestamp** of the error
3. **Full error response** (sanitize sensitive data)
4. **Steps to reproduce** the issue
5. **Your subscription tier** and usage patterns

Contact support at: support@zero-comp.com
"""
        
        self._write_file("error-handling.md", content)
    
    def _write_file(self, filename: str, content: str) -> None:
        """Write content to a documentation file."""
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {filename}")