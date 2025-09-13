"""Core data models for the solar weather API."""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class SeverityLevel(str, Enum):
    """Solar flare severity classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SubscriptionTier(str, Enum):
    """User subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SolarData(BaseModel):
    """Input data structure for solar weather predictions."""
    timestamp: datetime
    magnetic_field_data: List[float] = Field(..., description="Magnetic field measurements")
    solar_wind_speed: float = Field(..., ge=0, description="Solar wind speed in km/s")
    proton_density: float = Field(..., ge=0, description="Proton density in particles/cm³")
    temperature: float = Field(..., ge=0, description="Temperature in Kelvin")
    source: str = Field(default="nasa", description="Data source identifier")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }





class AlertResponse(BaseModel):
    """API response for solar flare alerts."""
    id: str = Field(..., description="Unique alert identifier")
    timestamp: datetime
    flare_probability: float = Field(..., ge=0.0, le=1.0)
    severity_level: SeverityLevel
    alert_triggered: bool = Field(..., description="Whether alert threshold was exceeded")
    message: str = Field(..., description="Human-readable alert message")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }





class CurrentAlertResponse(BaseModel):
    """Response for current alert status."""
    current_probability: float = Field(..., ge=0.0, le=1.0)
    severity_level: SeverityLevel
    last_updated: datetime
    next_update: datetime
    alert_active: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HistoricalAlertsResponse(BaseModel):
    """Response for historical alerts with pagination."""
    alerts: List[AlertResponse]
    total_count: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    has_more: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str = Field(..., description="Message type: alert, heartbeat, error")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(..., description="Unique request identifier")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserSubscription(BaseModel):
    """Extended user subscription model for database operations."""
    id: Optional[str] = Field(None, description="Subscription ID")
    user_id: str = Field(..., description="User ID from auth system")
    tier: SubscriptionTier = Field(default=SubscriptionTier.FREE)
    razorpay_subscription_id: Optional[str] = Field(None, description="Razorpay subscription ID")
    razorpay_customer_id: Optional[str] = Field(None, description="Razorpay customer ID")
    api_key_hash: Optional[str] = Field(None, description="Hashed API key")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    alert_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"low": 0.3, "medium": 0.6, "high": 0.8},
        description="Alert threshold probabilities"
    )
    is_active: bool = Field(default=True, description="Whether subscription is active")
    subscription_start_date: Optional[datetime] = Field(None, description="Subscription start date")
    subscription_end_date: Optional[datetime] = Field(None, description="Subscription end date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PredictionResult(BaseModel):
    """Extended prediction result model for database operations."""
    id: Optional[str] = Field(None, description="Prediction ID")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    flare_probability: float = Field(..., ge=0.0, le=1.0, description="Solar flare probability")
    severity_level: SeverityLevel = Field(..., description="Severity classification")
    model_version: str = Field(default="surya-1.0", description="Model version")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Model confidence")
    raw_output: Dict[str, Any] = Field(default_factory=dict, description="Raw model output")
    solar_data: Dict[str, Any] = Field(default_factory=dict, description="Input solar data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class APIUsageRecord(BaseModel):
    """API usage tracking record."""
    id: Optional[str] = Field(None, description="Usage record ID")
    user_id: Optional[str] = Field(None, description="User ID (None for anonymous)")
    subscription_id: Optional[str] = Field(None, description="Subscription ID")
    endpoint: str = Field(..., description="API endpoint called")
    method: str = Field(default="GET", description="HTTP method")
    status_code: int = Field(..., description="HTTP status code")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    request_size_bytes: Optional[int] = Field(None, description="Request size in bytes")
    response_size_bytes: Optional[int] = Field(None, description="Response size in bytes")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    api_key_used: bool = Field(default=False, description="Whether API key was used")
    rate_limit_hit: bool = Field(default=False, description="Whether rate limit was hit")
    timestamp: Optional[datetime] = Field(None, description="Request timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class HealthStatus(BaseModel):
    """Basic health status response."""
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ServiceHealth(BaseModel):
    """Individual service health status."""
    status: str = Field(..., description="Service status: healthy, unhealthy, degraded")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional service metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemMetrics(BaseModel):
    """System performance metrics."""
    cpu: Dict[str, Any] = Field(..., description="CPU usage metrics")
    memory: Dict[str, Any] = Field(..., description="Memory usage metrics")
    disk: Dict[str, Any] = Field(..., description="Disk usage metrics")
    process: Dict[str, Any] = Field(..., description="Process-specific metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertMetrics(BaseModel):
    """Alert system performance metrics."""
    total_predictions: int = Field(..., description="Total predictions made")
    successful_predictions: int = Field(..., description="Successful predictions")
    failed_predictions: int = Field(..., description="Failed predictions")
    average_inference_time_ms: float = Field(..., description="Average inference time")
    alerts_triggered: int = Field(..., description="Total alerts triggered")
    websocket_connections: int = Field(..., description="Active WebSocket connections")
    last_prediction_time: Optional[datetime] = Field(None, description="Last prediction timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }