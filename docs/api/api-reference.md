# ZERO-COMP Solar Weather API Reference


# ZERO-COMP Solar Weather API

Real-time solar flare prediction API powered by NASA-IBM's Surya-1.0 transformer model.

## Overview

ZERO-COMP provides enterprise-grade solar weather forecasting to industries that depend on space reliability, including:
- **Satellite Operators**: Protect satellite fleets from space weather damage
- **Power Grid Companies**: Plan maintenance windows and prevent outages
- **Aviation Firms**: Adjust polar flight routes during solar storms
- **Research Institutions**: Access historical solar weather data

## Features

- **Real-time Predictions**: Solar flare probability updates every 10 minutes
- **Multiple Access Methods**: REST API, WebSocket alerts, and web dashboard
- **Tiered Subscriptions**: Free, Pro ($50/month), and Enterprise ($500/month) plans
- **Historical Data**: Access to comprehensive solar weather history
- **Custom Alerts**: Configurable probability thresholds and webhook notifications

## Authentication

The API supports two authentication methods:

### 1. JWT Tokens (Dashboard Users)
Obtain JWT tokens through the web dashboard login process using Supabase authentication.

### 2. API Keys (Programmatic Access)
Generate API keys through the dashboard for programmatic access. API keys are available for Pro and Enterprise subscribers.

**Authentication Header Format:**
```
Authorization: Bearer <your-jwt-token-or-api-key>
```

## Rate Limits

Rate limits vary by subscription tier:

| Tier | Alerts Endpoint | History Endpoint | WebSocket |
|------|----------------|------------------|-----------|
| Free | 10/hour | 5/hour | Dashboard only |
| Pro | 1,000/hour | 500/hour | ✓ |
| Enterprise | 10,000/hour | 5,000/hour | ✓ |

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error_code": "HTTP_400",
  "message": "Invalid request parameters",
  "details": {},
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-string"
}
```

## WebSocket Real-time Alerts

Connect to `/ws/alerts` for real-time solar flare notifications:

```javascript
const ws = new WebSocket('wss://api.zero-comp.com/ws/alerts?token=your-jwt-token');
ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  if (alert.type === 'alert') {
    console.log('Solar flare alert:', alert.data);
  }
};
```

## Support

- **Documentation**: [https://docs.zero-comp.com](https://docs.zero-comp.com)
- **Support Email**: support@zero-comp.com
- **Status Page**: [https://status.zero-comp.com](https://status.zero-comp.com)
            

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


### /api/v1/alerts/current

#### GET /api/v1/alerts/current

**Get current solar flare prediction**

Returns the most recent solar flare probability prediction with severity classification.

**Responses:**

- `200`: Current solar flare prediction
- `401`: 
- `429`: 
- `500`: 


### /api/v1/alerts/history

#### GET /api/v1/alerts/history

**Get historical solar flare predictions**

Returns historical solar flare predictions with filtering and pagination support.

**Parameters:**

- `hours_back`: Number of hours to look back (1-168)
- `severity`: Filter by severity level
- `min_probability`: Minimum probability threshold (0.0-1.0)
- `page`: Page number for pagination
- `page_size`: Number of results per page

**Responses:**

- `200`: Historical solar flare predictions
- `400`: 
- `401`: 
- `429`: 
- `500`: 


### /ws/alerts

#### GET /ws/alerts

**WebSocket connection for real-time alerts**

Establish WebSocket connection for real-time solar flare notifications. Requires Pro or Enterprise subscription.

**Parameters:**

- `token` (required): JWT token for authentication

**Responses:**

- `101`: WebSocket connection established
- `401`: Authentication failed
- `403`: Insufficient subscription tier

