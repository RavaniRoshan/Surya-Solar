"""Subscription and payment related models."""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from app.models.core import SubscriptionTier


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"


class PaymentRecord(BaseModel):
    """Payment record model."""
    id: Optional[str] = Field(None, description="Payment record ID")
    user_id: str = Field(..., description="User ID")
    subscription_id: Optional[str] = Field(None, description="Associated subscription ID")
    razorpay_payment_id: Optional[str] = Field(None, description="Razorpay payment ID")
    razorpay_order_id: Optional[str] = Field(None, description="Razorpay order ID")
    amount: float = Field(..., ge=0, description="Payment amount in INR")
    currency: str = Field(default="INR", description="Payment currency")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    payment_method: Optional[str] = Field(None, description="Payment method used")
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    payment_date: Optional[datetime] = Field(None, description="Payment completion date")
    failure_reason: Optional[str] = Field(None, description="Failure reason if payment failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional payment metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SubscriptionPlan(BaseModel):
    """Subscription plan configuration."""
    tier: SubscriptionTier
    name: str = Field(..., description="Plan display name")
    description: str = Field(..., description="Plan description")
    price: float = Field(..., ge=0, description="Monthly price in INR")
    features: list[str] = Field(default_factory=list, description="Available features")
    rate_limits: Dict[str, Any] = Field(default_factory=dict, description="Rate limit configuration")
    razorpay_plan_id: Optional[str] = Field(None, description="Razorpay plan ID")


class PaymentLinkRequest(BaseModel):
    """Request model for creating payment links."""
    tier: SubscriptionTier = Field(..., description="Target subscription tier")
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: str = Field(..., description="Customer email address")
    callback_url: Optional[str] = Field(None, description="Payment success callback URL")
    notes: Dict[str, str] = Field(default_factory=dict, description="Additional notes")


class PaymentLinkResponse(BaseModel):
    """Response model for payment link creation."""
    payment_link_id: str = Field(..., description="Razorpay payment link ID")
    payment_url: str = Field(..., description="Payment URL for customer")
    amount: float = Field(..., description="Payment amount in INR")
    tier: SubscriptionTier = Field(..., description="Subscription tier")
    expires_at: Optional[datetime] = Field(None, description="Payment link expiration")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SubscriptionUpgradeRequest(BaseModel):
    """Request model for subscription upgrades."""
    target_tier: SubscriptionTier = Field(..., description="Target subscription tier")
    immediate: bool = Field(default=True, description="Whether to upgrade immediately")


class SubscriptionCancellationRequest(BaseModel):
    """Request model for subscription cancellation."""
    reason: Optional[str] = Field(None, max_length=500, description="Cancellation reason")
    cancel_immediately: bool = Field(default=False, description="Cancel immediately or at cycle end")


class WebhookEvent(BaseModel):
    """Razorpay webhook event model."""
    event_type: str = Field(..., description="Webhook event type")
    account_id: str = Field(..., description="Razorpay account ID")
    entity: str = Field(..., description="Entity type (payment, subscription, etc.)")
    contains: list[str] = Field(default_factory=list, description="Contained entities")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    created_at: datetime = Field(..., description="Event creation timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WebhookProcessingResult(BaseModel):
    """Result of webhook processing."""
    event_type: str = Field(..., description="Processed event type")
    processed: bool = Field(..., description="Whether event was successfully processed")
    user_id: Optional[str] = Field(None, description="Affected user ID")
    action: Optional[str] = Field(None, description="Action taken")
    subscription_id: Optional[str] = Field(None, description="Affected subscription ID")
    payment_id: Optional[str] = Field(None, description="Affected payment ID")
    tier: Optional[SubscriptionTier] = Field(None, description="Subscription tier")
    status: Optional[str] = Field(None, description="New status")
    amount: Optional[float] = Field(None, description="Payment amount")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional processing metadata")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SubscriptionDetails(BaseModel):
    """Detailed subscription information."""
    id: str = Field(..., description="Subscription ID")
    user_id: str = Field(..., description="User ID")
    tier: SubscriptionTier = Field(..., description="Current subscription tier")
    status: SubscriptionStatus = Field(..., description="Subscription status")
    razorpay_subscription_id: Optional[str] = Field(None, description="Razorpay subscription ID")
    razorpay_customer_id: Optional[str] = Field(None, description="Razorpay customer ID")
    current_period_start: Optional[datetime] = Field(None, description="Current billing period start")
    current_period_end: Optional[datetime] = Field(None, description="Current billing period end")
    next_billing_date: Optional[datetime] = Field(None, description="Next billing date")
    amount: float = Field(..., ge=0, description="Subscription amount")
    currency: str = Field(default="INR", description="Subscription currency")
    trial_end: Optional[datetime] = Field(None, description="Trial period end date")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation date")
    ended_at: Optional[datetime] = Field(None, description="Subscription end date")
    api_key: Optional[str] = Field(None, description="API key for this subscription")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    alert_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"low": 0.3, "medium": 0.6, "high": 0.8},
        description="Alert threshold configuration"
    )
    usage_stats: Dict[str, Any] = Field(default_factory=dict, description="Usage statistics")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }