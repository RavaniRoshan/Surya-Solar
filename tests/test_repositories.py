"""Unit tests for repository classes."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from app.repositories.predictions import PredictionsRepository
from app.repositories.subscriptions import SubscriptionsRepository
from app.repositories.api_usage import APIUsageRepository
from app.models.core import PredictionResult, SeverityLevel, UserSubscription, SubscriptionTier, APIUsageRecord


class TestPredictionsRepository:
    """Test cases for PredictionsRepository."""
    
    @pytest.fixture
    def predictions_repo(self):
        """Create PredictionsRepository instance for testing."""
        return PredictionsRepository()
    
    @pytest.fixture
    def mock_prediction_row(self):
        """Mock database row for prediction."""
        return {
            'id': 'pred-123',
            'timestamp': datetime.utcnow(),
            'flare_probability': 0.75,
            'severity_level': 'high',
            'model_version': 'surya-1.0',
            'confidence_score': 0.85,
            'raw_output': {'score': 0.75},
            'solar_data': {'wind_speed': 400},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    def test_row_to_model(self, predictions_repo, mock_prediction_row):
        """Test converting database row to PredictionResult model."""
        result = predictions_repo._row_to_model(mock_prediction_row)
        
        assert isinstance(result, PredictionResult)
        assert result.id == 'pred-123'
        assert result.flare_probability == 0.75
        assert result.severity_level == SeverityLevel.HIGH
        assert result.confidence_score == 0.85
    
    def test_model_to_dict(self, predictions_repo):
        """Test converting PredictionResult model to dictionary."""
        prediction = PredictionResult(
            id='pred-123',
            timestamp=datetime.utcnow(),
            flare_probability=0.75,
            severity_level=SeverityLevel.HIGH,
            confidence_score=0.85,
            raw_output={'score': 0.75},
            solar_data={'wind_speed': 400}
        )
        
        result = predictions_repo._model_to_dict(prediction)
        
        assert result['id'] == 'pred-123'
        assert result['flare_probability'] == 0.75
        assert result['severity_level'] == 'high'
        assert result['confidence_score'] == 0.85
    
    @pytest.mark.asyncio
    async def test_get_current_prediction(self, predictions_repo, mock_prediction_row):
        """Test getting current prediction."""
        predictions_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_db_manager.execute_query.return_value = mock_prediction_row
        predictions_repo._get_db_manager.return_value = mock_db_manager
        
        result = await predictions_repo.get_current_prediction()
        
        assert result is not None
        assert result.id == 'pred-123'
        assert result.severity_level == SeverityLevel.HIGH
        mock_db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_predictions_by_time_range(self, predictions_repo, mock_prediction_row):
        """Test getting predictions by time range."""
        predictions_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_db_manager.execute_query.return_value = [mock_prediction_row]
        predictions_repo._get_db_manager.return_value = mock_db_manager
        
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        results = await predictions_repo.get_predictions_by_time_range(start_time, end_time)
        
        assert len(results) == 1
        assert results[0].id == 'pred-123'
        mock_db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_predictions_by_severity(self, predictions_repo, mock_prediction_row):
        """Test getting predictions by severity level."""
        predictions_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_db_manager.execute_query.return_value = [mock_prediction_row]
        predictions_repo._get_db_manager.return_value = mock_db_manager
        
        results = await predictions_repo.get_predictions_by_severity(SeverityLevel.HIGH, hours_back=24)
        
        assert len(results) == 1
        assert results[0].severity_level == SeverityLevel.HIGH
        mock_db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_prediction_statistics(self, predictions_repo):
        """Test getting prediction statistics."""
        predictions_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_stats = {
            'total_predictions': 100,
            'avg_probability': 0.45,
            'max_probability': 0.95,
            'min_probability': 0.05,
            'high_count': 10,
            'medium_count': 30,
            'low_count': 60
        }
        mock_db_manager.execute_query.return_value = mock_stats
        predictions_repo._get_db_manager.return_value = mock_db_manager
        
        result = await predictions_repo.get_prediction_statistics(hours_back=24)
        
        assert result['total_predictions'] == 100
        assert result['avg_probability'] == 0.45
        assert result['high_severity_count'] == 10
        assert result['hours_analyzed'] == 24


class TestSubscriptionsRepository:
    """Test cases for SubscriptionsRepository."""
    
    @pytest.fixture
    def subscriptions_repo(self):
        """Create SubscriptionsRepository instance for testing."""
        return SubscriptionsRepository()
    
    @pytest.fixture
    def mock_subscription_row(self):
        """Mock database row for subscription."""
        return {
            'id': 'sub-123',
            'user_id': 'user-456',
            'tier': 'pro',
            'razorpay_subscription_id': 'rzp_sub_123',
            'razorpay_customer_id': 'rzp_cust_456',
            'api_key_hash': 'hash123',
            'webhook_url': 'https://example.com/webhook',
            'alert_thresholds': {'low': 0.3, 'medium': 0.6, 'high': 0.8},
            'is_active': True,
            'subscription_start_date': datetime.utcnow(),
            'subscription_end_date': None,
            'last_login': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    def test_row_to_model(self, subscriptions_repo, mock_subscription_row):
        """Test converting database row to UserSubscription model."""
        result = subscriptions_repo._row_to_model(mock_subscription_row)
        
        assert isinstance(result, UserSubscription)
        assert result.id == 'sub-123'
        assert result.user_id == 'user-456'
        assert result.tier == SubscriptionTier.PRO
        assert result.is_active is True
    
    def test_model_to_dict(self, subscriptions_repo):
        """Test converting UserSubscription model to dictionary."""
        subscription = UserSubscription(
            id='sub-123',
            user_id='user-456',
            tier=SubscriptionTier.PRO,
            is_active=True,
            alert_thresholds={'low': 0.3, 'medium': 0.6, 'high': 0.8}
        )
        
        result = subscriptions_repo._model_to_dict(subscription)
        
        assert result['id'] == 'sub-123'
        assert result['user_id'] == 'user-456'
        assert result['tier'] == 'pro'
        assert result['is_active'] is True
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self, subscriptions_repo, mock_subscription_row):
        """Test getting subscription by user ID."""
        subscriptions_repo.find_one_by_field = AsyncMock(return_value=subscriptions_repo._row_to_model(mock_subscription_row))
        
        result = await subscriptions_repo.get_by_user_id('user-456')
        
        assert result is not None
        assert result.user_id == 'user-456'
        subscriptions_repo.find_one_by_field.assert_called_once_with('user_id', 'user-456')
    
    @pytest.mark.asyncio
    async def test_get_active_subscriptions(self, subscriptions_repo, mock_subscription_row):
        """Test getting active subscriptions."""
        subscriptions_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_db_manager.execute_query.return_value = [mock_subscription_row]
        subscriptions_repo._get_db_manager.return_value = mock_db_manager
        
        results = await subscriptions_repo.get_active_subscriptions()
        
        assert len(results) == 1
        assert results[0].is_active is True
        mock_db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_subscription_tier(self, subscriptions_repo, mock_subscription_row):
        """Test updating subscription tier."""
        mock_subscription = subscriptions_repo._row_to_model(mock_subscription_row)
        subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        subscriptions_repo.update = AsyncMock(return_value=mock_subscription)
        
        result = await subscriptions_repo.update_subscription_tier('user-456', SubscriptionTier.ENTERPRISE)
        
        assert result is not None
        subscriptions_repo.get_by_user_id.assert_called_once_with('user-456')
        subscriptions_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_subscription(self, subscriptions_repo, mock_subscription_row):
        """Test deactivating subscription."""
        mock_subscription = subscriptions_repo._row_to_model(mock_subscription_row)
        subscriptions_repo.get_by_user_id = AsyncMock(return_value=mock_subscription)
        subscriptions_repo.update = AsyncMock(return_value=mock_subscription)
        
        result = await subscriptions_repo.deactivate_subscription('user-456')
        
        assert result is True
        subscriptions_repo.get_by_user_id.assert_called_once_with('user-456')
        subscriptions_repo.update.assert_called_once()


class TestAPIUsageRepository:
    """Test cases for APIUsageRepository."""
    
    @pytest.fixture
    def api_usage_repo(self):
        """Create APIUsageRepository instance for testing."""
        return APIUsageRepository()
    
    @pytest.fixture
    def mock_usage_row(self):
        """Mock database row for API usage."""
        return {
            'id': 'usage-123',
            'user_id': 'user-456',
            'subscription_id': 'sub-789',
            'endpoint': '/api/v1/alerts/current',
            'method': 'GET',
            'status_code': 200,
            'response_time_ms': 150,
            'request_size_bytes': 1024,
            'response_size_bytes': 2048,
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0',
            'api_key_used': True,
            'rate_limit_hit': False,
            'timestamp': datetime.utcnow()
        }
    
    def test_row_to_model(self, api_usage_repo, mock_usage_row):
        """Test converting database row to APIUsageRecord model."""
        result = api_usage_repo._row_to_model(mock_usage_row)
        
        assert isinstance(result, APIUsageRecord)
        assert result.id == 'usage-123'
        assert result.user_id == 'user-456'
        assert result.endpoint == '/api/v1/alerts/current'
        assert result.status_code == 200
        assert result.api_key_used is True
    
    def test_model_to_dict(self, api_usage_repo):
        """Test converting APIUsageRecord model to dictionary."""
        usage = APIUsageRecord(
            id='usage-123',
            user_id='user-456',
            endpoint='/api/v1/alerts/current',
            method='GET',
            status_code=200,
            response_time_ms=150,
            api_key_used=True,
            timestamp=datetime.utcnow()
        )
        
        result = api_usage_repo._model_to_dict(usage)
        
        assert result['id'] == 'usage-123'
        assert result['user_id'] == 'user-456'
        assert result['endpoint'] == '/api/v1/alerts/current'
        assert result['status_code'] == 200
        assert result['api_key_used'] is True
    
    @pytest.mark.asyncio
    async def test_log_api_call(self, api_usage_repo):
        """Test logging an API call."""
        mock_usage = APIUsageRecord(
            user_id='user-456',
            endpoint='/api/v1/alerts/current',
            method='GET',
            status_code=200,
            timestamp=datetime.utcnow()
        )
        api_usage_repo.create = AsyncMock(return_value=mock_usage)
        
        result = await api_usage_repo.log_api_call(
            user_id='user-456',
            endpoint='/api/v1/alerts/current',
            method='GET',
            status_code=200
        )
        
        assert result is not None
        assert result.user_id == 'user-456'
        api_usage_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_usage_by_user(self, api_usage_repo, mock_usage_row):
        """Test getting usage by user."""
        api_usage_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_db_manager.execute_query.return_value = [mock_usage_row]
        api_usage_repo._get_db_manager.return_value = mock_db_manager
        
        results = await api_usage_repo.get_usage_by_user('user-456', hours_back=24)
        
        assert len(results) == 1
        assert results[0].user_id == 'user-456'
        mock_db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_request_count(self, api_usage_repo):
        """Test getting user request count."""
        api_usage_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_db_manager.execute_query.return_value = {'count': 42}
        api_usage_repo._get_db_manager.return_value = mock_db_manager
        
        result = await api_usage_repo.get_user_request_count('user-456', hours_back=1)
        
        assert result == 42
        mock_db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_endpoint_statistics(self, api_usage_repo):
        """Test getting endpoint statistics."""
        api_usage_repo._get_db_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_stats = [{
            'endpoint': '/api/v1/alerts/current',
            'request_count': 100,
            'avg_response_time': 150.5,
            'max_response_time': 500,
            'success_count': 95,
            'error_count': 5,
            'rate_limit_hits': 2
        }]
        mock_db_manager.execute_query.return_value = mock_stats
        api_usage_repo._get_db_manager.return_value = mock_db_manager
        
        results = await api_usage_repo.get_endpoint_statistics(hours_back=24)
        
        assert len(results) == 1
        assert results[0]['endpoint'] == '/api/v1/alerts/current'
        assert results[0]['request_count'] == 100
        assert results[0]['success_rate'] == 95.0
        mock_db_manager.execute_query.assert_called_once()