# Getting Started with ZERO-COMP API

This guide will help you make your first API call and integrate solar weather alerts into your application.

## Quick Start

### 1. Sign Up and Get API Access

1. **Create Account**: Sign up at [https://dashboard.zero-comp.com](https://dashboard.zero-comp.com)
2. **Choose Plan**: Select Free (dashboard only), Pro ($50/month), or Enterprise ($500/month)
3. **Generate API Key**: Pro/Enterprise users can generate API keys for programmatic access

### 2. Make Your First API Call

```bash
# Get current solar flare probability
curl -H "Authorization: Bearer your-api-key" \
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
curl -H "Authorization: Bearer your-api-key" \
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
