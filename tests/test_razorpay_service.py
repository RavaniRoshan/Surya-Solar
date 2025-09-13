"""Tests for Razorpay service integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
import hmac
import hashlib
from datetime import datetime

from app.services.razorpay_service import RazorpayService, get_razorpay_service
from app.models.core import SubscriptionTier
from app.models.subscription import PaymentStatus, SubscriptionStatus


class TestRazorpayService:
    """Test cases for RazorpayService."""
    
    @pytest.fixture
    def mock_razorpay_client(self):
        """Mock Razorpay client."""
        with patch('app.services.razorpay_service.razorpay.Client') as mock_client:
            yield mock_client
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Razorpay configuration."""
        with patch('app.services.razorpay_service.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.external.razorpay_key_id = "test_key_id"
            mock_settings.external.razorpay_key_secret = "test_key_secret"
            mock_settings.external.razorpay_webhook_secret = "test_webhook_secret"
            mock_settings.subscription_tiers = {
                "free": {"price": 0, "features": ["dashboard"]},
                "pro": {"price": 50, "features": ["dashboard", "api"]},
                "enterprise": {"price": 500, "features": ["dashboard", "api", "sla"]}
            }
            mock_settings.api.cors_origins = ["http://localhost:3000"]
            mock_get_settings.return_value = mock_settings
            yield mock_settings
    
    @pytest.fixture
    def razorpay_service(self, mock_razorpay_client, mock_settings):
        """Create RazorpayService instance with mocked dependencies."""
        return RazorpayService()
    
    def test_initialization_with_credentials(self, mock_razorpay_client, mock_settings):
        """Test service initialization with valid credentials."""
        service = RazorpayService()
        
        assert service.is_configured() is True
        mock_razorpay_client.assert_called_once_with(
            auth=("test_key_id", "test_key_secret")
        )
    
    def test_initialization_without_credentials(self, mock_razorpay_client):
        """Test service initialization without credentials."""
        with patch('app.services.razorpay_service.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.external.razorpay_key_id = None
            mock_settings.external.razorpay_key_secret = None
            mock_get_settings.return_value = mock_settings
            
            service = RazorpayService()
            
            assert service.is_configured() is False
            assert service.client is None
    
    @pytest.mark.asyncio
    async def test_create_subscription_plan_pro(self, razorpay_service):
        """Test creating a subscription plan for Pro tier."""
        mock_plan = {
            "id": "plan_test123",
            "period": "monthly",
            "interval": 1,
            "item": {
                "amount": 5000,
                "currency": "INR"
            }
        }
        razorpay_service.client.plan.create.return_value = mock_plan
        
        result = await razorpay_service.create_subscription_plan(SubscriptionTier.PRO)
        
        assert result["id"] == "plan_test123"
        razorpay_service.client.plan.create.assert_called_once()
        
        # Verify the plan data structure
        call_args = razorpay_service.client.plan.create.call_args[0][0]
        assert call_args["period"] == "monthly"
        assert call_args["interval"] == 1
        assert call_args["item"]["amount"] == 5000  # 50 * 100 paise
        assert call_args["item"]["currency"] == "INR"
    
    @pytest.mark.asyncio
    async def test_create_subscription_plan_free(self, razorpay_service):
        """Test creating a subscription plan for Free tier."""
        result = await razorpay_service.create_subscription_plan(SubscriptionTier.FREE)
        
        assert result["id"] == "free"
        assert result["amount"] == 0
        # Should not call Razorpay API for free tier
        razorpay_service.client.plan.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_subscription_free_tier(self, razorpay_service):
        """Test creating a subscription for Free tier."""
        result = await razorpay_service.create_subscription(
            user_id="user123",
            tier=SubscriptionTier.FREE,
            customer_email="test@example.com",
            customer_name="Test User"
        )
        
        assert result["id"] == "free_user123"
        assert result["status"] == "active"
        # Should not call Razorpay API for free tier
        razorpay_service.client.customer.create.assert_not_called()
        razorpay_service.client.subscription.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_subscription_paid_tier(self, razorpay_service):
        """Test creating a subscription for paid tier."""
        mock_customer = {"id": "cust_test123"}
        mock_subscription = {
            "id": "sub_test123",
            "status": "created",
            "customer_id": "cust_test123"
        }
        
        razorpay_service.client.customer.create.return_value = mock_customer
        razorpay_service.client.subscription.create.return_value = mock_subscription
        
        result = await razorpay_service.create_subscription(
            user_id="user123",
            tier=SubscriptionTier.PRO,
            customer_email="test@example.com",
            customer_name="Test User"
        )
        
        assert result["id"] == "sub_test123"
        assert result["customer_id"] == "cust_test123"
        
        # Verify customer creation
        razorpay_service.client.customer.create.assert_called_once()
        customer_data = razorpay_service.client.customer.create.call_args[0][0]
        assert customer_data["email"] == "test@example.com"
        assert customer_data["name"] == "Test User"
        assert customer_data["notes"]["user_id"] == "user123"
        
        # Verify subscription creation
        razorpay_service.client.subscription.create.assert_called_once()
        subscription_data = razorpay_service.client.subscription.create.call_args[0][0]
        assert subscription_data["customer_id"] == "cust_test123"
        assert subscription_data["notes"]["user_id"] == "user123"
        assert subscription_data["notes"]["tier"] == "pro"
    
    @pytest.mark.asyncio
    async def test_create_payment_link(self, razorpay_service):
        """Test creating a payment link."""
        mock_payment_link = {
            "id": "plink_test123",
            "short_url": "https://rzp.io/i/test123",
            "amount": 5000,
            "created_at": 1640995200
        }
        
        razorpay_service.client.payment_link.create.return_value = mock_payment_link
        
        result = await razorpay_service.create_payment_link(
            tier=SubscriptionTier.PRO,
            user_id="user123",
            customer_email="test@example.com",
            customer_name="Test User"
        )
        
        assert result["id"] == "plink_test123"
        assert result["short_url"] == "https://rzp.io/i/test123"
        
        # Verify payment link data
        razorpay_service.client.payment_link.create.assert_called_once()
        link_data = razorpay_service.client.payment_link.create.call_args[0][0]
        assert link_data["amount"] == 5000  # 50 * 100 paise
        assert link_data["currency"] == "INR"
        assert link_data["customer"]["email"] == "test@example.com"
        assert link_data["notes"]["user_id"] == "user123"
        assert link_data["notes"]["tier"] == "pro"
    
    @pytest.mark.asyncio
    async def test_create_payment_link_free_tier_error(self, razorpay_service):
        """Test that creating payment link for free tier raises error."""
        with pytest.raises(ValueError, match="Cannot create payment link for free tier"):
            await razorpay_service.create_payment_link(
                tier=SubscriptionTier.FREE,
                user_id="user123",
                customer_email="test@example.com",
                customer_name="Test User"
            )
    
    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self, razorpay_service):
        """Test webhook signature verification with valid signature."""
        payload = b'{"event": "payment.captured"}'
        secret = "test_webhook_secret"
        
        # Create expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        result = await razorpay_service.verify_webhook_signature(payload, expected_signature)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(self, razorpay_service):
        """Test webhook signature verification with invalid signature."""
        payload = b'{"event": "payment.captured"}'
        invalid_signature = "invalid_signature"
        
        result = await razorpay_service.verify_webhook_signature(payload, invalid_signature)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_process_webhook_subscription_activated(self, razorpay_service):
        """Test processing subscription activated webhook."""
        webhook_data = {
            "event": "subscription.activated",
            "payload": {
                "subscription": {
                    "id": "sub_test123",
                    "status": "active",
                    "notes": {
                        "user_id": "user123",
                        "tier": "pro"
                    }
                }
            }
        }
        
        result = await razorpay_service.process_webhook_event(webhook_data)
        
        assert result["processed"] is True
        assert result["user_id"] == "user123"
        assert result["action"] == "activate_subscription"
        assert result["tier"] == "pro"
        assert result["subscription_id"] == "sub_test123"
        assert result["status"] == SubscriptionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_process_webhook_payment_captured(self, razorpay_service):
        """Test processing payment captured webhook."""
        webhook_data = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "id": "pay_test123",
                    "amount": 5000,
                    "notes": {
                        "user_id": "user123",
                        "tier": "pro"
                    }
                }
            }
        }
        
        result = await razorpay_service.process_webhook_event(webhook_data)
        
        assert result["processed"] is True
        assert result["user_id"] == "user123"
        assert result["action"] == "payment_captured"
        assert result["payment_id"] == "pay_test123"
        assert result["tier"] == "pro"
        assert result["amount"] == 50.0  # Converted from paise
        assert result["status"] == PaymentStatus.CAPTURED
    
    @pytest.mark.asyncio
    async def test_process_webhook_payment_failed(self, razorpay_service):
        """Test processing payment failed webhook."""
        webhook_data = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "id": "pay_test123",
                    "error_description": "Insufficient funds",
                    "notes": {
                        "user_id": "user123"
                    }
                }
            }
        }
        
        result = await razorpay_service.process_webhook_event(webhook_data)
        
        assert result["processed"] is True
        assert result["user_id"] == "user123"
        assert result["action"] == "payment_failed"
        assert result["payment_id"] == "pay_test123"
        assert result["status"] == PaymentStatus.FAILED
        assert result["error_description"] == "Insufficient funds"
    
    @pytest.mark.asyncio
    async def test_process_webhook_unhandled_event(self, razorpay_service):
        """Test processing unhandled webhook event type."""
        webhook_data = {
            "event": "unknown.event",
            "payload": {}
        }
        
        result = await razorpay_service.process_webhook_event(webhook_data)
        
        assert result["event_type"] == "unknown.event"
        assert result["processed"] is False
    
    @pytest.mark.asyncio
    async def test_get_subscription_details(self, razorpay_service):
        """Test getting subscription details from Razorpay."""
        mock_subscription = {
            "id": "sub_test123",
            "status": "active",
            "current_start": 1640995200,
            "current_end": 1643673600
        }
        
        razorpay_service.client.subscription.fetch.return_value = mock_subscription
        
        result = await razorpay_service.get_subscription_details("sub_test123")
        
        assert result["id"] == "sub_test123"
        assert result["status"] == "active"
        razorpay_service.client.subscription.fetch.assert_called_once_with("sub_test123")
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self, razorpay_service):
        """Test cancelling a subscription in Razorpay."""
        mock_result = {
            "id": "sub_test123",
            "status": "cancelled"
        }
        
        razorpay_service.client.subscription.cancel.return_value = mock_result
        
        result = await razorpay_service.cancel_subscription("sub_test123")
        
        assert result["id"] == "sub_test123"
        assert result["status"] == "cancelled"
        razorpay_service.client.subscription.cancel.assert_called_once_with(
            "sub_test123", 
            {"cancel_at_cycle_end": 0}
        )
    
    @pytest.mark.asyncio
    async def test_service_not_configured_errors(self):
        """Test that methods raise errors when service is not configured."""
        with patch('app.services.razorpay_service.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.external.razorpay_key_id = None
            mock_settings.external.razorpay_key_secret = None
            mock_get_settings.return_value = mock_settings
            
            service = RazorpayService()
            
            with pytest.raises(ValueError, match="Razorpay not configured"):
                await service.create_subscription_plan(SubscriptionTier.PRO)
            
            with pytest.raises(ValueError, match="Razorpay not configured"):
                await service.create_subscription("user123", SubscriptionTier.PRO, "test@example.com", "Test User")
            
            with pytest.raises(ValueError, match="Razorpay not configured"):
                await service.create_payment_link(SubscriptionTier.PRO, "user123", "test@example.com", "Test User")
            
            with pytest.raises(ValueError, match="Razorpay not configured"):
                await service.get_subscription_details("sub_test123")
            
            with pytest.raises(ValueError, match="Razorpay not configured"):
                await service.cancel_subscription("sub_test123")


def test_get_razorpay_service():
    """Test getting the global Razorpay service instance."""
    service = get_razorpay_service()
    assert isinstance(service, RazorpayService)
    
    # Should return the same instance
    service2 = get_razorpay_service()
    assert service is service2