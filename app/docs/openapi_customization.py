"""OpenAPI documentation customization and enhancement."""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def customize_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Customize OpenAPI schema with enhanced documentation, examples, and security schemes.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        Customized OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # Generate base OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from Supabase authentication or API key for programmatic access"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "API key in format: 'Bearer zc_your-api-key-here'"
        }
    }
    
    # Add comprehensive examples for request/response models
    _add_model_examples(openapi_schema)
    
    # Add rate limiting information to endpoints
    _add_rate_limit_info(openapi_schema)
    
    # Add subscription tier requirements
    _add_subscription_requirements(openapi_schema)
    
    # Add error response examples
    _add_error_examples(openapi_schema)
    
    # Add WebSocket documentation
    _add_websocket_documentation(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def _add_model_examples(schema: Dict[str, Any]) -> None:
    """Add comprehensive examples to data models."""
    
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    
    # Current Alert Response Example
    if "CurrentAlertResponse" in schemas:
        schemas["CurrentAlertResponse"]["example"] = {
            "current_probability": 0.75,
            "severity_level": "high",
            "last_updated": "2024-01-15T14:30:00Z",
            "next_update": "2024-01-15T14:40:00Z",
            "alert_active": True
        }
        
        # Add multiple examples for different scenarios
        schemas["CurrentAlertResponse"]["examples"] = {
            "high_severity": {
                "summary": "High severity solar flare alert",
                "value": {
                    "current_probability": 0.85,
                    "severity_level": "high",
                    "last_updated": "2024-01-15T14:30:00Z",
                    "next_update": "2024-01-15T14:40:00Z",
                    "alert_active": True
                }
            },
            "medium_severity": {
                "summary": "Medium severity prediction",
                "value": {
                    "current_probability": 0.55,
                    "severity_level": "medium",
                    "last_updated": "2024-01-15T14:30:00Z",
                    "next_update": "2024-01-15T14:40:00Z",
                    "alert_active": False
                }
            },
            "low_severity": {
                "summary": "Low severity prediction",
                "value": {
                    "current_probability": 0.25,
                    "severity_level": "low",
                    "last_updated": "2024-01-15T14:30:00Z",
                    "next_update": "2024-01-15T14:40:00Z",
                    "alert_active": False
                }
            }
        }
    
    # Historical Alerts Response Example
    if "HistoricalAlertsResponse" in schemas:
        schemas["HistoricalAlertsResponse"]["example"] = {
            "alerts": [
                {
                    "id": "alert_1705327800",
                    "timestamp": "2024-01-15T14:30:00Z",
                    "flare_probability": 0.85,
                    "severity_level": "high",
                    "alert_triggered": True,
                    "message": "High severity solar flare prediction: 85.0% probability"
                },
                {
                    "id": "alert_1705327200",
                    "timestamp": "2024-01-15T14:20:00Z", 
                    "flare_probability": 0.45,
                    "severity_level": "medium",
                    "alert_triggered": False,
                    "message": "Medium severity solar flare prediction: 45.0% probability"
                }
            ],
            "total_count": 144,
            "page": 1,
            "page_size": 50,
            "has_more": True
        }
        
        # Add examples for different filter scenarios
        schemas["HistoricalAlertsResponse"]["examples"] = {
            "recent_24h": {
                "summary": "Last 24 hours of predictions",
                "value": {
                    "alerts": [
                        {
                            "id": "alert_1705327800",
                            "timestamp": "2024-01-15T14:30:00Z",
                            "flare_probability": 0.85,
                            "severity_level": "high",
                            "alert_triggered": True,
                            "message": "High severity solar flare prediction: 85.0% probability"
                        }
                    ],
                    "total_count": 144,
                    "page": 1,
                    "page_size": 50,
                    "has_more": True
                }
            },
            "high_severity_only": {
                "summary": "High severity alerts only",
                "value": {
                    "alerts": [
                        {
                            "id": "alert_1705327800",
                            "timestamp": "2024-01-15T14:30:00Z",
                            "flare_probability": 0.85,
                            "severity_level": "high",
                            "alert_triggered": True,
                            "message": "High severity solar flare prediction: 85.0% probability"
                        },
                        {
                            "id": "alert_1705324200",
                            "timestamp": "2024-01-15T13:30:00Z",
                            "flare_probability": 0.92,
                            "severity_level": "high",
                            "alert_triggered": True,
                            "message": "High severity solar flare prediction: 92.0% probability"
                        }
                    ],
                    "total_count": 12,
                    "page": 1,
                    "page_size": 50,
                    "has_more": False
                }
            }
        }
    
    # User Profile Response Example
    if "UserProfileResponse" in schemas:
        schemas["UserProfileResponse"]["example"] = {
            "user_id": "user_123456789",
            "email": "user@example.com",
            "subscription_tier": "pro",
            "api_key_exists": True,
            "webhook_url": "https://your-app.com/webhooks/solar-alerts",
            "alert_thresholds": {
                "low": 0.3,
                "medium": 0.6,
                "high": 0.8
            },
            "subscription_start_date": "2024-01-01T00:00:00Z",
            "subscription_end_date": "2024-02-01T00:00:00Z",
            "last_login": "2024-01-15T14:25:00Z",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    # Error Response Example
    if "ErrorResponse" in schemas:
        schemas["ErrorResponse"]["example"] = {
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


def _add_rate_limit_info(schema: Dict[str, Any]) -> None:
    """Add rate limiting information to endpoint descriptions."""
    
    rate_limit_info = """

## Rate Limits

This endpoint has different rate limits based on your subscription tier:

| Tier | Rate Limit | 
|------|------------|
| Free | 10 requests/hour |
| Pro | 1,000 requests/hour |
| Enterprise | 10,000 requests/hour |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window  
- `X-RateLimit-Reset`: Unix timestamp when window resets
"""
    
    # Add to alert endpoints
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        if "/alerts/" in path:
            for method, details in methods.items():
                if "description" in details:
                    details["description"] += rate_limit_info


def _add_subscription_requirements(schema: Dict[str, Any]) -> None:
    """Add subscription tier requirements to endpoints."""
    
    tier_requirements = {
        "/api/v1/alerts/export/csv": "**Enterprise Only**: This endpoint requires Enterprise subscription.",
        "/api/v1/users/api-key": "**Pro/Enterprise**: API key generation requires Pro or Enterprise subscription.",
        "/ws/alerts": "**Pro/Enterprise**: WebSocket access requires Pro or Enterprise subscription."
    }
    
    paths = schema.get("paths", {})
    for path, requirement in tier_requirements.items():
        if path in paths:
            for method, details in paths[path].items():
                if "description" in details:
                    details["description"] = requirement + "\n\n" + details["description"]


def _add_error_examples(schema: Dict[str, Any]) -> None:
    """Add common error response examples to endpoints."""
    
    common_errors = {
        "400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_PARAMETERS",
                        "message": "Invalid request parameters",
                        "details": {"field": "hours_back", "error": "must be between 1 and 168"},
                        "timestamp": "2024-01-15T14:30:00Z",
                        "request_id": "req_abc123def456"
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "AUTHENTICATION_REQUIRED",
                        "message": "Valid authentication credentials required",
                        "details": {"hint": "Include 'Authorization: Bearer <token>' header"},
                        "timestamp": "2024-01-15T14:30:00Z",
                        "request_id": "req_abc123def456"
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INSUFFICIENT_SUBSCRIPTION",
                        "message": "This feature requires Pro or Enterprise subscription",
                        "details": {"current_tier": "free", "required_tier": "pro"},
                        "timestamp": "2024-01-15T14:30:00Z",
                        "request_id": "req_abc123def456"
                    }
                }
            }
        },
        "429": {
            "description": "Rate Limit Exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded for your subscription tier",
                        "details": {"limit": 10, "window": "1 hour", "retry_after": 3600},
                        "timestamp": "2024-01-15T14:30:00Z",
                        "request_id": "req_abc123def456"
                    }
                }
            }
        },
        "500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {},
                        "timestamp": "2024-01-15T14:30:00Z",
                        "request_id": "req_abc123def456"
                    }
                }
            }
        }
    }
    
    # Add error examples to all endpoints
    paths = schema.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if "responses" not in details:
                details["responses"] = {}
            
            # Add common error responses
            for status_code, error_spec in common_errors.items():
                if status_code not in details["responses"]:
                    details["responses"][status_code] = error_spec


def _add_websocket_documentation(schema: Dict[str, Any]) -> None:
    """Add WebSocket-specific documentation."""
    
    # Add WebSocket message examples
    websocket_examples = {
        "connection_message": {
            "type": "connection",
            "data": {
                "connection_id": "conn_abc123",
                "authenticated": True,
                "subscription_tier": "pro",
                "message": "Connected successfully"
            },
            "timestamp": "2024-01-15T14:30:00Z"
        },
        "alert_message": {
            "type": "alert", 
            "data": {
                "id": "alert_1705327800",
                "timestamp": "2024-01-15T14:30:00Z",
                "flare_probability": 0.85,
                "severity_level": "high",
                "alert_triggered": True,
                "message": "High severity solar flare prediction: 85.0% probability"
            },
            "timestamp": "2024-01-15T14:30:00Z"
        },
        "heartbeat_message": {
            "type": "heartbeat",
            "data": {"status": "alive"},
            "timestamp": "2024-01-15T14:30:00Z"
        },
        "error_message": {
            "type": "error",
            "data": {
                "error_code": "AUTHENTICATION_FAILED",
                "message": "Invalid or expired token"
            },
            "timestamp": "2024-01-15T14:30:00Z"
        }
    }
    
    # Add WebSocket message schema
    if "components" not in schema:
        schema["components"] = {}
    if "schemas" not in schema["components"]:
        schema["components"]["schemas"] = {}
    
    schema["components"]["schemas"]["WebSocketExamples"] = {
        "type": "object",
        "description": "WebSocket message examples",
        "examples": websocket_examples
    }


def add_code_examples() -> Dict[str, Dict[str, str]]:
    """Generate code examples for different programming languages."""
    
    return {
        "python": {
            "get_current_alert": '''
import requests

# Using JWT token
headers = {"Authorization": "Bearer your-jwt-token"}
response = requests.get("https://api.zero-comp.com/api/v1/alerts/current", headers=headers)
alert = response.json()

print(f"Solar flare probability: {alert['current_probability']:.1%}")
print(f"Severity: {alert['severity_level']}")
print(f"Alert active: {alert['alert_active']}")
            ''',
            "websocket_connection": '''
import asyncio
import websockets
import json

async def connect_to_alerts():
    uri = "wss://api.zero-comp.com/ws/alerts?token=your-jwt-token"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to ZERO-COMP alerts")
        
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "alert":
                alert = data["data"]
                print(f"🚨 Solar flare alert: {alert['flare_probability']:.1%} probability")
            elif data["type"] == "heartbeat":
                print("💓 Heartbeat received")

# Run the WebSocket client
asyncio.run(connect_to_alerts())
            ''',
            "api_key_usage": '''
import requests

# Using API key
headers = {"Authorization": "Bearer zc_your-api-key-here"}

# Get current alert
current = requests.get("https://api.zero-comp.com/api/v1/alerts/current", headers=headers)
print("Current alert:", current.json())

# Get 24 hours of history
history = requests.get(
    "https://api.zero-comp.com/api/v1/alerts/history",
    headers=headers,
    params={"hours_back": 24, "min_probability": 0.5}
)
print(f"Found {len(history.json()['alerts'])} high-probability alerts")
            '''
        },
        "javascript": {
            "get_current_alert": '''
// Using fetch API
const response = await fetch('https://api.zero-comp.com/api/v1/alerts/current', {
  headers: {
    'Authorization': 'Bearer your-jwt-token'
  }
});

const alert = await response.json();
console.log(`Solar flare probability: ${(alert.current_probability * 100).toFixed(1)}%`);
console.log(`Severity: ${alert.severity_level}`);
console.log(`Alert active: ${alert.alert_active}`);
            ''',
            "websocket_connection": '''
// WebSocket connection for real-time alerts
const ws = new WebSocket('wss://api.zero-comp.com/ws/alerts?token=your-jwt-token');

ws.onopen = () => {
  console.log('Connected to ZERO-COMP alerts');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'alert') {
    const alert = data.data;
    console.log(`🚨 Solar flare alert: ${(alert.flare_probability * 100).toFixed(1)}% probability`);
    
    // Show browser notification
    if (Notification.permission === 'granted') {
      new Notification('Solar Flare Alert', {
        body: `${alert.severity_level.toUpperCase()} severity: ${(alert.flare_probability * 100).toFixed(1)}% probability`,
        icon: '/solar-flare-icon.png'
      });
    }
  } else if (data.type === 'heartbeat') {
    console.log('💓 Heartbeat received');
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
            ''',
            "node_js_example": '''
// Node.js example using axios
const axios = require('axios');

const client = axios.create({
  baseURL: 'https://api.zero-comp.com',
  headers: {
    'Authorization': 'Bearer zc_your-api-key-here'
  }
});

async function getSolarWeatherData() {
  try {
    // Get current alert
    const current = await client.get('/api/v1/alerts/current');
    console.log('Current solar flare probability:', current.data.current_probability);
    
    // Get historical data
    const history = await client.get('/api/v1/alerts/history', {
      params: {
        hours_back: 24,
        severity: 'high'
      }
    });
    
    console.log(`Found ${history.data.alerts.length} high-severity alerts in last 24 hours`);
    
  } catch (error) {
    if (error.response?.status === 429) {
      console.error('Rate limit exceeded. Retry after:', error.response.headers['x-ratelimit-reset']);
    } else {
      console.error('API error:', error.response?.data || error.message);
    }
  }
}

getSolarWeatherData();
            '''
        },
        "curl": {
            "get_current_alert": '''
# Get current solar flare alert
curl -H "Authorization: Bearer your-jwt-token" \\
     https://api.zero-comp.com/api/v1/alerts/current
            ''',
            "get_history": '''
# Get 24 hours of historical data with high severity filter
curl -H "Authorization: Bearer zc_your-api-key-here" \\
     "https://api.zero-comp.com/api/v1/alerts/history?hours_back=24&severity=high&page=1&page_size=50"
            ''',
            "generate_api_key": '''
# Generate new API key (requires JWT token from dashboard login)
curl -X POST \\
     -H "Authorization: Bearer your-jwt-token" \\
     https://api.zero-comp.com/api/v1/users/api-key
            ''',
            "export_csv": '''
# Export historical data as CSV (Enterprise only)
curl -H "Authorization: Bearer zc_your-api-key-here" \\
     "https://api.zero-comp.com/api/v1/alerts/export/csv?hours_back=168&min_probability=0.7" \\
     -o solar_flare_data.csv
            '''
        }
    }