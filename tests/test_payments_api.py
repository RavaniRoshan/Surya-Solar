"""Tests for payment API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime

from app.main import create_app
from app.models.core import SubscriptionTier
from app.models.subscription import PaymentLinkRequest, SubscriptionUpgradeRequest


class TestPaymentsAPI:
    """Test cases for payments API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authentication."""
        return {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User"
        }
    
    @pytest.fixture
    def mock_razorpay_service(self):
        """Mock Razorpay service."""
        mock_service = Mock()
        mock_service.is_configured.return_value = True
        return mock_service
    
    @pytest.fixture
    def mock_subscription_repo(self):
        """Mock subscription repository."""
        return Mock()
    
    def test_create_payment_link_success(self, client, mock_current_user, mock_razorpay_service):
        """Test successful payment link creation."""
        # Mock dependencies
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            # Mock Razorpay response
            mock_payment_link = {
                "id": "plink_test123",
                "short_url": "https://rzp.io/i/test123",
                "amount": 5000,
                "created_at": 1640995200,
                "expire_by": 1641081600
            }
            mock_razorpay_service.create_payment_link = AsyncMock(return_value=mock_payment_link)
            
            # Make request
            response = client.post(
                "/api/v1/payments/create-payment-link",
                json={
                    "tier": "pro",
                    "customer_name": "Test User",
                    "customer_email": "test@example.com"
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["payment_link_id"] == "plink_test123"
            assert data["payment_url"] == "https://rzp.io/i/test123"
            assert data["amount"] == 50.0  # Converted from paise
            assert data["tier"] == "pro"
            
            # Verify service was called correctly
            mock_razorpay_service.create_payment_link.assert_called_once_with(
                tier=SubscriptionTier.PRO,
                user_id="user123",
                customer_email="test@example.com",
                customer_name="Test User"
            )
    
    def test_create_payment_link_service_unavailable(self, client, mock_current_user, mock_razorpay_service):
        """Test payment link creation when service is unavailable."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            # Mock service as not configured
            mock_razorpay_service.is_configured.return_value = False
            
            response = client.post(
                "/api/v1/payments/create-payment-link",
                json={
                    "tier": "pro",
                    "customer_name": "Test User",
                    "customer_email": "test@example.com"
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 503
            assert "Payment processing is currently unavailable" in response.json()["detail"]
    
    def test_create_payment_link_service_error(self, client, mock_current_user, mock_razorpay_service):
        """Test payment link creation with service error."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            # Mock service error
            mock_razorpay_service.create_payment_link = AsyncMock(side_effect=Exception("Service error"))
            
            response = client.post(
                "/api/v1/payments/create-payment-link",
                json={
                    "tier": "pro",
                    "customer_name": "Test User",
                    "customer_email": "test@example.com"
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 500
            assert "Failed to create payment link" in response.json()["detail"]
    
    def test_upgrade_subscription(self, client, mock_current_user, mock_razorpay_service):
        """Test subscription upgrade request."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            response = client.post(
                "/api/v1/payments/upgrade-subscription",
                json={
                    "target_tier": "enterprise",
                    "immediate": True
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["target_tier"] == "enterprise"
            assert data["next_step"] == "create_payment_link"
    
    def test_upgrade_subscription_to_free_error(self, client, mock_current_user, mock_razorpay_service):
        """Test that upgrading to free tier returns error."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            response = client.post(
                "/api/v1/payments/upgrade-subscription",
                json={
                    "target_tier": "free",
                    "immediate": True
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 400
            assert "Cannot upgrade to free tier" in response.json()["detail"]
    
    def test_cancel_subscription_success(self, client, mock_current_user, mock_razorpay_service, mock_subscription_repo):
        """Test successful subscription cancellation."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service), \
             patch('app.api.payments.get_subscriptions_repository', return_value=mock_subscription_repo):
            
            # Mock subscription
            mock_subscription = Mock()
            mock_subscription.id = "sub123"
            mock_subscription.tier = SubscriptionTier.PRO
            mock_subscription.razorpay_subscription_id = "rzp_sub123"
            mock_subscription_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
            mock_subscription_repo.cancel_subscription = AsyncMock(return_value=True)
            
            # Mock Razorpay cancellation
            mock_razorpay_service.cancel_subscription = AsyncMock(return_value={"status": "cancelled"})
            
            response = client.post(
                "/api/v1/payments/cancel-subscription",
                json={
                    "reason": "No longer needed",
                    "cancel_immediately": True
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Subscription cancelled successfully" in data["message"]
            assert data["cancelled_immediately"] is True
            
            # Verify service calls
            mock_razorpay_service.cancel_subscription.assert_called_once_with("rzp_sub123")
            mock_subscription_repo.cancel_subscription.assert_called_once_with(
                "sub123",
                reason="No longer needed",
                immediate=True
            )
    
    def test_cancel_subscription_no_subscription(self, client, mock_current_user, mock_razorpay_service, mock_subscription_repo):
        """Test cancellation when no subscription exists."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service), \
             patch('app.api.payments.get_subscriptions_repository', return_value=mock_subscription_repo):
            
            # Mock no subscription found
            mock_subscription_repo.get_by_user_id = AsyncMock(return_value=None)
            
            response = client.post(
                "/api/v1/payments/cancel-subscription",
                json={
                    "reason": "No longer needed",
                    "cancel_immediately": True
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 404
            assert "No active subscription found" in response.json()["detail"]
    
    def test_cancel_subscription_free_tier_error(self, client, mock_current_user, mock_razorpay_service, mock_subscription_repo):
        """Test that cancelling free tier returns error."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service), \
             patch('app.api.payments.get_subscriptions_repository', return_value=mock_subscription_repo):
            
            # Mock free tier subscription
            mock_subscription = Mock()
            mock_subscription.tier = SubscriptionTier.FREE
            mock_subscription_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
            
            response = client.post(
                "/api/v1/payments/cancel-subscription",
                json={
                    "reason": "No longer needed",
                    "cancel_immediately": True
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 400
            assert "Cannot cancel free tier" in response.json()["detail"]
    
    def test_get_subscription_details_success(self, client, mock_current_user, mock_subscription_repo):
        """Test getting subscription details."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_subscriptions_repository', return_value=mock_subscription_repo):
            
            # Mock subscription
            mock_subscription = Mock()
            mock_subscription.id = "sub123"
            mock_subscription.user_id = "user123"
            mock_subscription.tier = SubscriptionTier.PRO
            mock_subscription.is_active = True
            mock_subscription.razorpay_subscription_id = "rzp_sub123"
            mock_subscription.razorpay_customer_id = "cust123"
            mock_subscription.subscription_start_date = datetime(2024, 1, 1)
            mock_subscription.subscription_end_date = datetime(2024, 2, 1)
            mock_subscription.api_key_hash = "hashed_key"
            mock_subscription.webhook_url = "https://example.com/webhook"
            mock_subscription.alert_thresholds = {"low": 0.3, "medium": 0.6, "high": 0.8}
            mock_subscription.created_at = datetime(2024, 1, 1)
            mock_subscription.updated_at = datetime(2024, 1, 1)
            
            mock_subscription_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
            
            response = client.get(
                "/api/v1/payments/subscription-details",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == "sub123"
            assert data["user_id"] == "user123"
            assert data["tier"] == "pro"
            assert data["status"] == "active"
            assert data["amount"] == 50  # Pro tier price
            assert data["api_key"] == "hashed_key"
            assert data["webhook_url"] == "https://example.com/webhook"
    
    def test_get_subscription_details_not_found(self, client, mock_current_user, mock_subscription_repo):
        """Test getting subscription details when none exists."""
        with patch('app.api.payments.get_current_user', return_value=mock_current_user), \
             patch('app.api.payments.get_subscriptions_repository', return_value=mock_subscription_repo):
            
            mock_subscription_repo.get_by_user_id = AsyncMock(return_value=None)
            
            response = client.get(
                "/api/v1/payments/subscription-details",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 404
            assert "No subscription found" in response.json()["detail"]
    
    def test_razorpay_webhook_success(self, client, mock_razorpay_service):
        """Test successful webhook processing."""
        with patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            # Mock webhook verification and processing
            mock_razorpay_service.verify_webhook_signature = AsyncMock(return_value=True)
            
            webhook_payload = {
                "event": "payment.captured",
                "payload": {
                    "payment": {
                        "id": "pay_test123",
                        "amount": 5000
                    }
                }
            }
            
            response = client.post(
                "/api/v1/payments/webhook",
                json=webhook_payload,
                headers={"X-Razorpay-Signature": "valid_signature"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["event_type"] == "payment.captured"
            assert data["processed"] is True
            assert data["action"] == "queued_for_processing"
            
            # Verify signature verification was called
            mock_razorpay_service.verify_webhook_signature.assert_called_once()
    
    def test_razorpay_webhook_invalid_signature(self, client, mock_razorpay_service):
        """Test webhook with invalid signature."""
        with patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            # Mock invalid signature
            mock_razorpay_service.verify_webhook_signature = AsyncMock(return_value=False)
            
            webhook_payload = {
                "event": "payment.captured",
                "payload": {}
            }
            
            response = client.post(
                "/api/v1/payments/webhook",
                json=webhook_payload,
                headers={"X-Razorpay-Signature": "invalid_signature"}
            )
            
            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]
    
    def test_razorpay_webhook_invalid_json(self, client, mock_razorpay_service):
        """Test webhook with invalid JSON payload."""
        with patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            # Mock valid signature but invalid JSON will be handled by FastAPI
            mock_razorpay_service.verify_webhook_signature = AsyncMock(return_value=True)
            
            response = client.post(
                "/api/v1/payments/webhook",
                data="invalid json",
                headers={
                    "X-Razorpay-Signature": "valid_signature",
                    "Content-Type": "application/json"
                }
            )
            
            # FastAPI will return 422 for invalid JSON
            assert response.status_code == 422
    
    def test_get_subscription_plans(self, client):
        """Test getting available subscription plans."""
        response = client.get("/api/v1/payments/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        plans = data["plans"]
        
        # Should have 3 plans
        assert len(plans) == 3
        
        # Check plan structure
        plan_tiers = [plan["tier"] for plan in plans]
        assert "free" in plan_tiers
        assert "pro" in plan_tiers
        assert "enterprise" in plan_tiers
        
        # Check free plan
        free_plan = next(plan for plan in plans if plan["tier"] == "free")
        assert free_plan["price"] == 0
        assert "dashboard" in free_plan["features"]
    
    def test_payment_health_check(self, client, mock_razorpay_service):
        """Test payment service health check."""
        with patch('app.api.payments.get_razorpay_service', return_value=mock_razorpay_service):
            
            mock_razorpay_service.is_configured.return_value = True
            
            response = client.get("/api/v1/payments/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["razorpay_configured"] is True
            assert "timestamp" in data