# ZERO-COMP Python SDK Integration Guide

This guide provides comprehensive instructions for integrating the ZERO-COMP Solar Weather API Python SDK into your applications.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Framework Integration](#framework-integration)
9. [Deployment Considerations](#deployment-considerations)
10. [Troubleshooting](#troubleshooting)

## Installation

### Requirements

- Python 3.7 or higher
- `requests` library for synchronous operations
- `aiohttp` library for asynchronous operations
- `websockets` library for real-time alerts

### Install Dependencies

```bash
pip install requests aiohttp websockets
```

### Install the SDK

```bash
# If published to PyPI
pip install zerocomp-sdk

# Or install from source
git clone https://github.com/your-org/zerocomp-sdk
cd zerocomp-sdk
pip install -e .
```

## Quick Start

### 1. Get Your API Key

1. Sign up at [ZERO-COMP Dashboard](https://dashboard.zero-comp.com)
2. Navigate to API Keys section
3. Generate a new API key
4. Store it securely (environment variable recommended)

### 2. Basic Example

```python
import os
from zerocomp_sdk import ZeroCompClient

# Initialize client
api_key = os.getenv('ZEROCOMP_API_KEY')
client = ZeroCompClient(api_key=api_key)

# Get current solar flare probability
alert = client.get_current_alert()
print(f"Solar flare probability: {alert.current_probability:.1%}")
print(f"Severity: {alert.severity_level.value}")
```

## Authentication

### API Key Authentication

The SDK uses Bearer token authentication with your API key:

```python
from zerocomp_sdk import ZeroCompClient

# Method 1: Pass API key directly
client = ZeroCompClient(api_key="your-api-key-here")

# Method 2: Use environment variable (recommended)
import os
client = ZeroCompClient(api_key=os.getenv('ZEROCOMP_API_KEY'))

# Method 3: Load from configuration file
import json
with open('config.json') as f:
    config = json.load(f)
client = ZeroCompClient(api_key=config['api_key'])
```

### Environment Variables

Create a `.env` file:

```bash
ZEROCOMP_API_KEY=your-api-key-here
ZEROCOMP_BASE_URL=https://api.zero-comp.com  # Optional
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('ZEROCOMP_API_KEY')
```

## Basic Usage

### Synchronous Client

```python
from zerocomp_sdk import ZeroCompClient, SeverityLevel

client = ZeroCompClient(api_key=api_key)

# Get current alert
current = client.get_current_alert()
print(f"Probability: {current.current_probability:.1%}")

# Get historical data
history = client.get_alert_history(
    hours_back=48,
    severity=SeverityLevel.HIGH,
    page_size=100
)
print(f"Found {len(history.alerts)} high-severity alerts")

# Get statistics
stats = client.get_alert_statistics(hours_back=24)
print(f"Average probability: {stats['statistics']['avg_probability']:.1%}")
```

### Asynchronous Client

```python
import asyncio
from zerocomp_sdk import AsyncZeroCompClient

async def main():
    async with AsyncZeroCompClient(api_key=api_key) as client:
        # Get current alert
        current = await client.get_current_alert()
        
        # Get multiple data points concurrently
        tasks = [
            client.get_alert_history(hours_back=24),
            client.get_alert_statistics(hours_back=24),
            client.get_user_profile()
        ]
        
        history, stats, profile = await asyncio.gather(*tasks)
        
        print(f"Current: {current.current_probability:.1%}")
        print(f"History: {len(history.alerts)} alerts")
        print(f"Subscription: {profile.subscription_tier.value}")

# Run async function
asyncio.run(main())
```

## Advanced Features

### Real-time WebSocket Monitoring

```python
import asyncio
from zerocomp_sdk import WebSocketClient

async def monitor_alerts():
    async with WebSocketClient(token=api_key) as ws:
        print("Connected to ZERO-COMP WebSocket")
        
        async for message in ws.listen():
            if message.get('type') == 'alert':
                alert_data = message['data']
                probability = alert_data['flare_probability']
                
                if alert_data['alert_triggered']:
                    print(f"🚨 ALERT: {probability:.1%} probability!")
                    # Send notifications, trigger actions, etc.
                    await send_notification(alert_data)

async def send_notification(alert_data):
    # Your notification logic here
    pass

asyncio.run(monitor_alerts())
```

### CSV Data Export (Enterprise)

```python
from datetime import datetime

# Export last 30 days of data
csv_data = client.export_csv(
    hours_back=720,  # 30 days
    min_probability=0.5,
    severity=SeverityLevel.MEDIUM
)

# Save to file
filename = f"solar_data_{datetime.now().strftime('%Y%m%d')}.csv"
with open(filename, 'wb') as f:
    f.write(csv_data)

print(f"Data exported to {filename}")
```

### User Profile Management

```python
# Get current profile
profile = client.get_user_profile()
print(f"Subscription: {profile.subscription_tier.value}")
print(f"API calls remaining: {profile.rate_limits}")

# Update webhook URL
updated_profile = client.update_profile(
    webhook_url="https://your-app.com/webhooks/solar-alerts",
    alert_thresholds={
        "low": 0.3,
        "medium": 0.6,
        "high": 0.8
    }
)

# Generate new API key
new_key_data = client.generate_api_key()
print(f"New API key: {new_key_data['api_key']}")
```

## Error Handling

### Exception Types

```python
from zerocomp_sdk import (
    ZeroCompAPIError,
    AuthenticationError,
    RateLimitError,
    SubscriptionError
)

try:
    alert = client.get_current_alert()
    
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
    print("Check your API key")
    
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
    print(f"Retry after {e.retry_after} seconds")
    
except SubscriptionError as e:
    print(f"Subscription insufficient: {e.message}")
    print(f"Required tier: {e.details.get('required_tier')}")
    
except ZeroCompAPIError as e:
    print(f"API error: {e.message}")
    print(f"Status code: {e.status_code}")
    print(f"Error code: {e.error_code}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

```python
import time
from zerocomp_sdk import RateLimitError

def get_alert_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.get_current_alert()
            
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = e.retry_after or 60
            print(f"Rate limited, waiting {wait_time} seconds...")
            time.sleep(wait_time)
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Error occurred, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
```

## Best Practices

### 1. Configuration Management

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ZeroCompConfig:
    api_key: str
    base_url: str = "https://api.zero-comp.com"
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'ZeroCompConfig':
        return cls(
            api_key=os.getenv('ZEROCOMP_API_KEY'),
            base_url=os.getenv('ZEROCOMP_BASE_URL', cls.base_url),
            timeout=int(os.getenv('ZEROCOMP_TIMEOUT', cls.timeout)),
            max_retries=int(os.getenv('ZEROCOMP_MAX_RETRIES', cls.max_retries))
        )

# Usage
config = ZeroCompConfig.from_env()
client = ZeroCompClient(
    api_key=config.api_key,
    base_url=config.base_url,
    timeout=config.timeout,
    max_retries=config.max_retries
)
```

### 2. Connection Pooling

```python
import asyncio
from zerocomp_sdk import AsyncZeroCompClient

class ZeroCompService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    async def __aenter__(self):
        self._client = AsyncZeroCompClient(api_key=self.api_key)
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_current_alert(self):
        return await self._client.get_current_alert()
    
    async def get_history(self, **kwargs):
        return await self._client.get_alert_history(**kwargs)

# Usage
async with ZeroCompService(api_key) as service:
    alert = await service.get_current_alert()
    history = await service.get_history(hours_back=24)
```

### 3. Caching

```python
import time
from functools import wraps
from typing import Dict, Any, Optional

class SimpleCache:
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())

# Global cache instance
cache = SimpleCache(ttl=300)  # 5 minutes

def cached_api_call(cache_key: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Make API call
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

@cached_api_call("current_alert")
def get_cached_current_alert(client):
    return client.get_current_alert()
```

## Framework Integration

### Django Integration

```python
# settings.py
ZEROCOMP_API_KEY = os.getenv('ZEROCOMP_API_KEY')
ZEROCOMP_BASE_URL = os.getenv('ZEROCOMP_BASE_URL', 'https://api.zero-comp.com')

# services.py
from django.conf import settings
from zerocomp_sdk import ZeroCompClient

class SolarWeatherService:
    def __init__(self):
        self.client = ZeroCompClient(
            api_key=settings.ZEROCOMP_API_KEY,
            base_url=settings.ZEROCOMP_BASE_URL
        )
    
    def get_current_alert(self):
        return self.client.get_current_alert()
    
    def get_alert_history(self, hours_back=24):
        return self.client.get_alert_history(hours_back=hours_back)

# views.py
from django.http import JsonResponse
from .services import SolarWeatherService

def current_alert_view(request):
    service = SolarWeatherService()
    try:
        alert = service.get_current_alert()
        return JsonResponse({
            'probability': alert.current_probability,
            'severity': alert.severity_level.value,
            'alert_active': alert.alert_active,
            'last_updated': alert.last_updated.isoformat()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

### Flask Integration

```python
from flask import Flask, jsonify, request
from zerocomp_sdk import ZeroCompClient, ZeroCompAPIError
import os

app = Flask(__name__)

# Initialize client
client = ZeroCompClient(api_key=os.getenv('ZEROCOMP_API_KEY'))

@app.route('/api/solar/current')
def get_current_alert():
    try:
        alert = client.get_current_alert()
        return jsonify({
            'probability': alert.current_probability,
            'severity': alert.severity_level.value,
            'alert_active': alert.alert_active,
            'last_updated': alert.last_updated.isoformat()
        })
    except ZeroCompAPIError as e:
        return jsonify({'error': e.message}), e.status_code or 500

@app.route('/api/solar/history')
def get_alert_history():
    hours_back = request.args.get('hours_back', 24, type=int)
    severity = request.args.get('severity')
    
    try:
        history = client.get_alert_history(
            hours_back=hours_back,
            severity=severity
        )
        return jsonify({
            'alerts': [
                {
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'probability': alert.flare_probability,
                    'severity': alert.severity_level.value,
                    'triggered': alert.alert_triggered
                }
                for alert in history.alerts
            ],
            'total_count': history.total_count,
            'has_more': history.has_more
        })
    except ZeroCompAPIError as e:
        return jsonify({'error': e.message}), e.status_code or 500

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from zerocomp_sdk import AsyncZeroCompClient, ZeroCompAPIError
import os

app = FastAPI(title="Solar Weather API Proxy")

class AlertResponse(BaseModel):
    probability: float
    severity: str
    alert_active: bool
    last_updated: str

@app.get("/solar/current", response_model=AlertResponse)
async def get_current_alert():
    async with AsyncZeroCompClient(api_key=os.getenv('ZEROCOMP_API_KEY')) as client:
        try:
            alert = await client.get_current_alert()
            return AlertResponse(
                probability=alert.current_probability,
                severity=alert.severity_level.value,
                alert_active=alert.alert_active,
                last_updated=alert.last_updated.isoformat()
            )
        except ZeroCompAPIError as e:
            raise HTTPException(status_code=e.status_code or 500, detail=e.message)

@app.post("/solar/webhook")
async def webhook_handler(alert_data: dict, background_tasks: BackgroundTasks):
    # Process webhook data
    background_tasks.add_task(process_alert, alert_data)
    return {"status": "received"}

async def process_alert(alert_data: dict):
    # Your alert processing logic
    pass
```

### Celery Integration

```python
from celery import Celery
from zerocomp_sdk import ZeroCompClient
import os

app = Celery('solar_weather_tasks')

@app.task
def check_solar_weather():
    client = ZeroCompClient(api_key=os.getenv('ZEROCOMP_API_KEY'))
    
    try:
        alert = client.get_current_alert()
        
        if alert.alert_active and alert.severity_level.value == 'high':
            # Send notifications
            send_high_severity_alert.delay(alert.current_probability)
        
        return {
            'probability': alert.current_probability,
            'severity': alert.severity_level.value,
            'alert_active': alert.alert_active
        }
        
    except Exception as e:
        # Log error and retry
        check_solar_weather.retry(countdown=60, max_retries=3)

@app.task
def send_high_severity_alert(probability):
    # Send email, SMS, push notifications, etc.
    pass

# Schedule periodic checks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-solar-weather': {
        'task': 'check_solar_weather',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
}
```

## Deployment Considerations

### Environment Variables

```bash
# Production environment
ZEROCOMP_API_KEY=prod-api-key-here
ZEROCOMP_BASE_URL=https://api.zero-comp.com
ZEROCOMP_TIMEOUT=30
ZEROCOMP_MAX_RETRIES=3

# Development environment
ZEROCOMP_API_KEY=dev-api-key-here
ZEROCOMP_BASE_URL=https://dev-api.zero-comp.com
```

### Docker Configuration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV ZEROCOMP_API_KEY=""
ENV ZEROCOMP_BASE_URL="https://api.zero-comp.com"

CMD ["python", "app.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: solar-weather-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: solar-weather-app
  template:
    metadata:
      labels:
        app: solar-weather-app
    spec:
      containers:
      - name: app
        image: your-app:latest
        env:
        - name: ZEROCOMP_API_KEY
          valueFrom:
            secretKeyRef:
              name: zerocomp-secret
              key: api-key
        - name: ZEROCOMP_BASE_URL
          value: "https://api.zero-comp.com"
---
apiVersion: v1
kind: Secret
metadata:
  name: zerocomp-secret
type: Opaque
data:
  api-key: <base64-encoded-api-key>
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

```python
# Check API key format
if not api_key or not api_key.startswith('zc_'):
    print("Invalid API key format")

# Test authentication
try:
    client = ZeroCompClient(api_key=api_key)
    profile = client.get_user_profile()
    print(f"Authentication successful: {profile.email}")
except AuthenticationError:
    print("Authentication failed - check your API key")
```

#### 2. Rate Limiting

```python
# Check rate limits
try:
    usage = client.get_usage_statistics()
    print(f"Current usage: {usage['current_period']}")
    print(f"Rate limits: {usage['rate_limits']}")
except Exception as e:
    print(f"Could not get usage stats: {e}")
```

#### 3. Network Issues

```python
# Test connectivity
try:
    health = client.health_check()
    print(f"API health: {health['status']}")
except Exception as e:
    print(f"Connectivity issue: {e}")
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('zerocomp_sdk')

# Create client with debug info
client = ZeroCompClient(
    api_key=api_key,
    timeout=60,  # Increase timeout for debugging
    max_retries=1  # Reduce retries for faster debugging
)
```

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            print(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

@monitor_performance
def get_alert_with_monitoring(client):
    return client.get_current_alert()
```

## Support

- **Documentation**: [https://docs.zero-comp.com](https://docs.zero-comp.com)
- **API Reference**: [https://api.zero-comp.com/docs](https://api.zero-comp.com/docs)
- **Support Email**: support@zero-comp.com
- **GitHub Issues**: [https://github.com/zero-comp/python-sdk/issues](https://github.com/zero-comp/python-sdk/issues)

## License

This SDK is licensed under the MIT License. See LICENSE file for details.