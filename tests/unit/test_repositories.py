"""Unit tests for repository classes."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Optional

from app.repositories.predictions import PredictionsRepository
from app.repositories.subscriptions import SubscriptionsRepository
from app.repositories.api_usage import APIUsageRepository
from app.models.core import PredictionResult, SeverityLevel, SubscriptionTier


class TestPredictionsRepository:
    """Test PredictionsRepository class."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table = MagicMock()
        return mock_client
    
    @pytest.fixture
    def predictions_repo(self, mock_supabase_client):
        """Create PredictionsRepository instance."""
        repo = PredictionsRepository()
        repo.supabase = mock_supabase_client
        return repo
    
    @pytest.fixture
    def sample_prediction(self):
        """Sample prediction data."""
        return PredictionResult(
            id="pred-123",
            timestamp=datetime.utcnow(),
            flare_probability=0.75,
            severity_level=SeverityLevel.HIGH,
            model_version="surya-1.0",
            confidence_score=0.85,
            raw_output={"test": "data"},
            solar_data={"magnetic_field": [1.0, 2.0, 3.0]}
        )
    
    @pytest.mark.asyncio
    async def test_create_prediction(self, predictions_repo, mock_supabase_client, sample_prediction):
        """Test creating a new prediction."""
        mock_table = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "pred-123"}]
        )
        mock_supabase_client.table.return_value = mock_table
        
        result = await predictions_repo.create(sample_prediction)
        
        assert result == "pred-123"
        mock_table.insert.assert_called_once()
        
        # Verify the data structure passed to insert
        insert_call = mock_table.insert.call_args[0][0]
        assert insert_call["flare_probability"] == 0.75
        assert insert_call["severity_level"] == "high"
        assert insert_call["model_version"] == "surya-1.0"
    
    @pytest.mark.asyncio
    async def test_get_current_prediction(self, predictions_repo, mock_supabase_client):
        """Test getting the most recent prediction."""
        mock_data = {
            "id": "pred-123",
            "timestamp": datetime.utcnow().isoformat(),
            "flare_probability": 0.75,
            "severity_level": "high",
            "model_version": "surya-1.0",
            "confidence_score": 0.85,
            "raw_output": {"test": "data"},
            "solar_data": {"magnetic_field": [1.0, 2.0, 3.0]}
        }
        
        mock_table = MagicMock()
        mock_table.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[mock_data]
        )
        mock_supabase_client.table.return_value = mock_table
        
        result = await predictions_repo.get_current_prediction()
        
        assert result is not None
        assert result.id == "pred-123"
        assert result.flare_probability == 0.75
        assert result.severity_level == SeverityLevel.HIGH
        
        # Verify query structure
        mock_table.select.assert_called_once()
        mock_table.select.return_value.order.assert_called_once_with("timestamp", desc=True)
        mock_table.select.return_value.order.return_value.limit.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_current_prediction_none(self, predictions_repo, mock_supabase_client):
        """Test getting current prediction when none exists."""
        mock_table = MagicMock()
        mock_table.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )
        mock_supabase_client.table.return_value = mock_table
        
        result = await predictions_repo.get_current_prediction()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_predictions_by_time_range(self, predictions_repo, mock_supabase_client):
        """Test getting predictions by time range."""
        start_time = datetime.utcnow() - timedelta(hours=24)
        end_time = datetime.utcnow()
        
        mock_data = [
            {
                "id": f"pred-{i}",
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "flare_probability": 0.5 + (i * 0.1),
                "severity_level": "medium",
                "model_version": "surya-1.0"
            }
            for i in range(3)
        ]
        
        mock_table = MagicMock()
        mock_table.select.return_value.gte.return_value.lte.return_value.order.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        mock_supabase_client.table.return_value = mock_table
        
        results = await predictions_repo.get_predictions_by_time_range(start_time, end_time)
        
        assert len(results) == 3
        assert all(isinstance(r, PredictionResult) for r in results)
        
        # Verify query structure
        mock_table.select.return_value.gte.assert_called_once_with("timestamp", start_time.isoformat())
        mock_table.select.return_value.gte.return_value.lte.assert_called_once_with("timestamp", end_time.isoformat())
    
    @pytest.mark.asyncio
    async def test_get_predictions_by_severity(self, predictions_repo, mock_supabase_client):
        """Test getting predictions by severity level."""
        mock_data = [
            {
                "id": "pred-high-1",
                "timestamp": datetime.utcnow().isoformat(),
                "flare_probability": 0.9,
                "severity_level": "high",
                "model_version": "surya-1.0"
            }
        ]
        
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        mock_supabase_client.table.return_value = mock_table
        
        results = await predictions_repo.get_predictions_by_severity(SeverityLevel.HIGH, hours_back=24)
        
        assert len(results) == 1
        assert results[0].severity_level == SeverityLevel.HIGH
        
        # Verify query filters
        mock_table.select.return_value.eq.assert_called_once_with("severity_level", "high")
    
    @pytest.mark.asyncio
    async def test_get_predictions_above_threshold(self, predictions_repo, mock_supabase_client):
        """Test getting predictions above probability threshold."""
        mock_data = [
            {
                "id": "pred-high-prob",
                "timestamp": datetime.utcnow().isoformat(),
                "flare_probability": 0.85,
                "severity_level": "high",
                "model_version": "surya-1.0"
            }
        ]
        
        mock_table = MagicMock()
        mock_table.select.return_value.gte.return_value.gte.return_value.order.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        mock_supabase_client.table.return_value = mock_table
        
        results = await predictions_repo.get_predictions_above_threshold(0.8, hours_back=24)
        
        assert len(results) == 1
        assert results[0].flare_probability == 0.85
    
    @pytest.mark.asyncio
    async def test_get_prediction_statistics(self, predictions_repo, mock_supabase_client):
        """Test getting prediction statistics."""
        mock_stats = {
            "total_predictions": 100,
            "avg_probability": 0.45,
            "max_probability": 0.95,
            "min_probability": 0.05,
            "high_severity_count": 10,
            "medium_severity_count": 30,
            "low_severity_count": 60
        }
        
        # Mock the RPC call for statistics
        mock_supabase_client.rpc.return_value.execute.return_value = MagicMock(
            data=[mock_stats]
        )
        
        stats = await predictions_repo.get_prediction_statistics(hours_back=24)
        
        assert stats["total_predictions"] == 100
        assert stats["avg_probability"] == 0.45
        assert stats["high_severity_count"] == 10
        
        mock_supabase_client.rpc.assert_called_once_with("get_prediction_statistics", {"hours_back": 24})
    
    @pytest.mark.asyncio
    async def test_get_hourly_prediction_counts(self, predictions_repo, mock_supabase_client):
        """Test getting hourly prediction counts."""
        mock_hourly_data = [
            {"hour": "2024-01-01T12:00:00Z", "prediction_count": 10},
            {"hour": "2024-01-01T13:00:00Z", "prediction_count": 12},
            {"hour": "2024-01-01T14:00:00Z", "prediction_count": 8}
        ]
        
        mock_supabase_client.rpc.return_value.execute.return_value = MagicMock(
            data=mock_hourly_data
        )
        
        hourly_counts = await predictions_repo.get_hourly_prediction_counts(hours_back=24)
        
        assert len(hourly_counts) == 3
        assert hourly_counts[0]["prediction_count"] == 10
        
        mock_supabase_client.rpc.assert_called_once_with("get_hourly_prediction_counts", {"hours_back": 24})
    
    @pytest.mark.asyncio
    async def test_delete_old_predictions(self, predictions_repo, mock_supabase_client):
        """Test deleting old predictions."""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        mock_table = MagicMock()
        mock_table.delete.return_value.lt.return_value.execute.return_value = MagicMock(
            data={"count": 50}
        )
        mock_supabase_client.table.return_value = mock_table
        
        deleted_count = await predictions_repo.delete_old_predictions(cutoff_date)
        
        assert deleted_count == 50
        mock_table.delete.return_value.lt.assert_called_once_with("timestamp", cutoff_date.isoformat())


class TestSubscriptionsRepository:
    """Test SubscriptionsRepository class."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table = MagicMock()
        return mock_client
    
    @pytest.fixture
    def subscriptions_repo(self, mock_supabase_client):
        """Create SubscriptionsRepository instance."""
        repo = SubscriptionsRepository()
        repo.supabase = mock_supabase_client
        return repo
    
    @pytest.mark.asyncio
    async def test_create_subscription(self, subscriptions_repo, mock_supabase_client):
        """Test creating a new subscription."""
        subscription_data = {
            "user_id": "user-123",
            "tier": "pro",
            "razorpay_subscription_id": "sub_123",
            "api_key_hash": "hashed_key",
            "webhook_url": "https://example.com/webhook"
        }
        
        mock_table = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "subscription-123"}]
        )
        mock_supabase_client.table.return_value = mock_table
        
        result = await subscriptions_repo.create_subscription(subscription_data)
        
        assert result == "subscription-123"
        mock_table.insert.assert_called_once_with(subscription_data)
    
    @pytest.mark.asyncio
    async def test_get_subscription_by_user_id(self, subscriptions_repo, mock_supabase_client):
        """Test getting subscription by user ID."""
        mock_data = {
            "id": "subscription-123",
            "user_id": "user-123",
            "tier": "pro",
            "api_key_hash": "hashed_key",
            "webhook_url": "https://example.com/webhook",
            "alert_thresholds": {"high": 0.8, "medium": 0.6},
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        mock_supabase_client.table.return_value = mock_table
        
        subscription = await subscriptions_repo.get_subscription_by_user_id("user-123")
        
        assert subscription is not None
        assert subscription["tier"] == "pro"
        assert subscription["webhook_url"] == "https://example.com/webhook"
        
        mock_table.select.return_value.eq.assert_called_once_with("user_id", "user-123")
    
    @pytest.mark.asyncio
    async def test_update_subscription_tier(self, subscriptions_repo, mock_supabase_client):
        """Test updating subscription tier."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        result = await subscriptions_repo.update_subscription_tier("user-123", "enterprise")
        
        assert result is True
        mock_table.update.assert_called_once_with({"tier": "enterprise", "updated_at": "now()"})
        mock_table.update.return_value.eq.assert_called_once_with("user_id", "user-123")
    
    @pytest.mark.asyncio
    async def test_update_api_key_hash(self, subscriptions_repo, mock_supabase_client):
        """Test updating API key hash."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        result = await subscriptions_repo.update_api_key_hash("user-123", "new_hashed_key")
        
        assert result is True
        mock_table.update.assert_called_once_with({"api_key_hash": "new_hashed_key", "updated_at": "now()"})
    
    @pytest.mark.asyncio
    async def test_update_webhook_url(self, subscriptions_repo, mock_supabase_client):
        """Test updating webhook URL."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        webhook_url = "https://newwebhook.com/endpoint"
        result = await subscriptions_repo.update_webhook_url("user-123", webhook_url)
        
        assert result is True
        mock_table.update.assert_called_once_with({"webhook_url": webhook_url, "updated_at": "now()"})
    
    @pytest.mark.asyncio
    async def test_update_alert_thresholds(self, subscriptions_repo, mock_supabase_client):
        """Test updating alert thresholds."""
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()
        mock_supabase_client.table.return_value = mock_table
        
        thresholds = {"high": 0.9, "medium": 0.7, "low": 0.3}
        result = await subscriptions_repo.update_alert_thresholds("user-123", thresholds)
        
        assert result is True
        mock_table.update.assert_called_once_with({"alert_thresholds": thresholds, "updated_at": "now()"})
    
    @pytest.mark.asyncio
    async def test_get_subscriptions_by_tier(self, subscriptions_repo, mock_supabase_client):
        """Test getting all subscriptions by tier."""
        mock_data = [
            {"user_id": "user-1", "tier": "pro"},
            {"user_id": "user-2", "tier": "pro"}
        ]
        
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        mock_supabase_client.table.return_value = mock_table
        
        subscriptions = await subscriptions_repo.get_subscriptions_by_tier("pro")
        
        assert len(subscriptions) == 2
        assert all(sub["tier"] == "pro" for sub in subscriptions)
        
        mock_table.select.return_value.eq.assert_called_once_with("tier", "pro")
    
    @pytest.mark.asyncio
    async def test_get_active_webhooks(self, subscriptions_repo, mock_supabase_client):
        """Test getting subscriptions with active webhooks."""
        mock_data = [
            {"user_id": "user-1", "webhook_url": "https://example1.com/webhook"},
            {"user_id": "user-2", "webhook_url": "https://example2.com/webhook"}
        ]
        
        mock_table = MagicMock()
        mock_table.select.return_value.not_.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        mock_supabase_client.table.return_value = mock_table
        
        webhooks = await subscriptions_repo.get_active_webhooks()
        
        assert len(webhooks) == 2
        assert all("webhook_url" in webhook for webhook in webhooks)
        
        mock_table.select.return_value.not_.assert_called_once()


class TestAPIUsageRepository:
    """Test APIUsageRepository class."""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table = MagicMock()
        return mock_client
    
    @pytest.fixture
    def api_usage_repo(self, mock_supabase_client):
        """Create APIUsageRepository instance."""
        repo = APIUsageRepository()
        repo.supabase = mock_supabase_client
        return repo
    
    @pytest.mark.asyncio
    async def test_create_usage_record(self, api_usage_repo, mock_supabase_client):
        """Test creating a usage record."""
        usage_data = {
            "user_id": "user-123",
            "endpoint": "/api/v1/alerts/current",
            "timestamp": datetime.utcnow(),
            "response_time_ms": 150,
            "status_code": 200
        }
        
        mock_table = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "usage-123"}]
        )
        mock_supabase_client.table.return_value = mock_table
        
        result = await api_usage_repo.create(usage_data)
        
        assert result == "usage-123"
        mock_table.insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_usage_count(self, api_usage_repo, mock_supabase_client):
        """Test getting usage count for a user."""
        mock_supabase_client.rpc.return_value.execute.return_value = MagicMock(
            data=[{"count": 25}]
        )
        
        count = await api_usage_repo.get_usage_count("user-123", hours_back=1)
        
        assert count == 25
        mock_supabase_client.rpc.assert_called_once_with(
            "get_user_api_usage_count",
            {"user_id": "user-123", "hours_back": 1}
        )
    
    @pytest.mark.asyncio
    async def test_get_usage_statistics(self, api_usage_repo, mock_supabase_client):
        """Test getting usage statistics."""
        mock_stats = {
            "total_requests": 1000,
            "avg_response_time_ms": 180,
            "error_rate": 0.02,
            "most_used_endpoint": "/api/v1/alerts/current"
        }
        
        mock_supabase_client.rpc.return_value.execute.return_value = MagicMock(
            data=[mock_stats]
        )
        
        stats = await api_usage_repo.get_usage_statistics("user-123", hours_back=24)
        
        assert stats["total_requests"] == 1000
        assert stats["avg_response_time_ms"] == 180
        assert stats["error_rate"] == 0.02
        
        mock_supabase_client.rpc.assert_called_once_with(
            "get_user_usage_statistics",
            {"user_id": "user-123", "hours_back": 24}
        )
    
    @pytest.mark.asyncio
    async def test_get_endpoint_usage(self, api_usage_repo, mock_supabase_client):
        """Test getting usage by endpoint."""
        mock_data = [
            {"endpoint": "/api/v1/alerts/current", "request_count": 500},
            {"endpoint": "/api/v1/alerts/history", "request_count": 300}
        ]
        
        mock_supabase_client.rpc.return_value.execute.return_value = MagicMock(
            data=mock_data
        )
        
        endpoint_usage = await api_usage_repo.get_endpoint_usage("user-123", hours_back=24)
        
        assert len(endpoint_usage) == 2
        assert endpoint_usage[0]["request_count"] == 500
        
        mock_supabase_client.rpc.assert_called_once_with(
            "get_endpoint_usage_breakdown",
            {"user_id": "user-123", "hours_back": 24}
        )
    
    @pytest.mark.asyncio
    async def test_cleanup_old_usage_records(self, api_usage_repo, mock_supabase_client):
        """Test cleaning up old usage records."""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        mock_table = MagicMock()
        mock_table.delete.return_value.lt.return_value.execute.return_value = MagicMock(
            data={"count": 1000}
        )
        mock_supabase_client.table.return_value = mock_table
        
        deleted_count = await api_usage_repo.cleanup_old_usage_records(cutoff_date)
        
        assert deleted_count == 1000
        mock_table.delete.return_value.lt.assert_called_once_with("timestamp", cutoff_date.isoformat())


class TestErrorHandling:
    """Test error handling in repositories."""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        repo = PredictionsRepository()
        
        with patch.object(repo, 'supabase') as mock_supabase:
            mock_supabase.table.side_effect = Exception("Connection failed")
            
            result = await repo.get_current_prediction()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self):
        """Test handling of malformed data from database."""
        repo = PredictionsRepository()
        
        with patch.object(repo, 'supabase') as mock_supabase:
            mock_table = MagicMock()
            mock_table.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"invalid": "structure"}]  # Missing required fields
            )
            mock_supabase.table.return_value = mock_table
            
            # Should handle gracefully and return None
            result = await repo.get_current_prediction()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_empty_result_handling(self):
        """Test handling of empty results from database."""
        repo = SubscriptionsRepository()
        
        with patch.object(repo, 'supabase') as mock_supabase:
            mock_table = MagicMock()
            mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data=None
            )
            mock_supabase.table.return_value = mock_table
            
            result = await repo.get_subscription_by_user_id("nonexistent-user")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_insert_failure_handling(self):
        """Test handling of insert failures."""
        repo = APIUsageRepository()
        
        with patch.object(repo, 'supabase') as mock_supabase:
            mock_table = MagicMock()
            mock_table.insert.return_value.execute.side_effect = Exception("Insert failed")
            mock_supabase.table.return_value = mock_table
            
            usage_data = {
                "user_id": "user-123",
                "endpoint": "/api/v1/alerts/current",
                "timestamp": datetime.utcnow()
            }
            
            result = await repo.create(usage_data)
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__])