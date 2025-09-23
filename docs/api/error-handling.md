# Error Handling Guide

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
