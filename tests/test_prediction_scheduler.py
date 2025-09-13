"""Integration tests for the prediction scheduler."""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.prediction_scheduler import (
    PredictionScheduler,
    SchedulerConfig,
    NASADataFetcher,
    get_prediction_scheduler,
    start_prediction_scheduler,
    stop_prediction_scheduler
)
from app.models.core import SolarData, PredictionResult, SeverityLevel


class TestSchedulerConfig:
    """Test SchedulerConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SchedulerConfig()
        
        assert config.prediction_interval_minutes == 10
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 30
        assert config.nasa_api_timeout_seconds == 30
        assert config.enable_mock_data is True
        assert "nasa.gov" in config.nasa_api_base_url
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SchedulerConfig(
            prediction_interval_minutes=5,
            max_retries=5,
            enable_mock_data=False
        )
        
        assert config.prediction_interval_minutes == 5
        assert config.max_retries == 5
        assert config.enable_mock_data is False


class TestNASADataFetcher:
    """Test NASADataFetcher class."""
    
    @pytest.fixture
    def data_fetcher(self):
        """Create a NASA data fetcher for testing."""
        config = SchedulerConfig(enable_mock_data=True)
        return NASADataFetcher(config)
    
    @pytest.mark.asyncio
    async def test_fetch_mock_data(self, data_fetcher):
        """Test fetching mock solar data."""
        solar_data = await data_fetcher.fetch_latest_solar_data()
        
        assert isinstance(solar_data, SolarData)
        assert solar_data.source == "nasa_mock"
        assert len(solar_data.magnetic_field_data) > 0
        assert 0 <= solar_data.solar_wind_speed <= 3000
        assert 0 <= solar_data.proton_density <= 1000
        assert 0 <= solar_data.temperature <= 10_000_000
        assert isinstance(solar_data.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_fetch_mock_data_consistency(self, data_fetcher):
        """Test that mock data generation is consistent."""
        data1 = await data_fetcher.fetch_latest_solar_data()
        data2 = await data_fetcher.fetch_latest_solar_data()
        
        # Data should be different (random) but valid
        assert isinstance(data1, SolarData)
        assert isinstance(data2, SolarData)
        assert data1.source == data2.source == "nasa_mock"
    
    @pytest.mark.asyncio
    async def test_fetch_real_data_placeholder(self):
        """Test real NASA data fetching (placeholder implementation)."""
        config = SchedulerConfig(enable_mock_data=False)
        fetcher = NASADataFetcher(config)
        
        # This should fail since we don't have real NASA API access
        with pytest.raises(RuntimeError):
            await fetcher.fetch_latest_solar_data()
        
        await fetcher.close()
    
    @pytest.mark.asyncio
    async def test_close_client(self, data_fetcher):
        """Test closing the HTTP client."""
        # Should not raise any exceptions
        await data_fetcher.close()


class TestPredictionScheduler:
    """Test PredictionScheduler class."""
    
    @pytest.fixture
    def scheduler_config(self):
        """Create a test scheduler configuration."""
        return SchedulerConfig(
            prediction_interval_minutes=1,  # Short interval for testing
            max_retries=2,
            retry_delay_seconds=1,
            enable_mock_data=True
        )
    
    @pytest_asyncio.fixture
    async def scheduler(self, scheduler_config):
        """Create a prediction scheduler for testing."""
        scheduler = PredictionScheduler(scheduler_config)
        
        # Mock the database dependency
        mock_repo = AsyncMock()
        mock_prediction = AsyncMock()
        mock_prediction.id = "test-prediction-id"
        mock_repo.create = AsyncMock(return_value=mock_prediction)
        mock_repo.get_current_prediction = AsyncMock(return_value=None)
        
        scheduler.prediction_repository = mock_repo
        
        yield scheduler
        
        # Cleanup
        if scheduler._running:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_initialization(self, scheduler_config):
        """Test scheduler initialization."""
        scheduler = PredictionScheduler(scheduler_config)
        
        assert scheduler.config == scheduler_config
        assert not scheduler._running
        assert scheduler._task is None
        assert scheduler.prediction_repository is None
    
    @pytest.mark.asyncio
    async def test_fetch_solar_data(self, scheduler):
        """Test fetching solar data."""
        solar_data = await scheduler.fetch_solar_data()
        
        assert isinstance(solar_data, SolarData)
        assert solar_data.source == "nasa_mock"
        assert len(solar_data.magnetic_field_data) > 0
    
    @pytest.mark.asyncio
    async def test_run_model_inference(self, scheduler):
        """Test running model inference."""
        # Create test solar data
        solar_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[1.0, 2.0, 3.0],
            solar_wind_speed=450.0,
            proton_density=8.5,
            temperature=1_500_000.0,
            source="test"
        )
        
        prediction_result = await scheduler._run_model_inference(solar_data)
        
        assert isinstance(prediction_result, PredictionResult)
        assert 0.0 <= prediction_result.flare_probability <= 1.0
        assert prediction_result.severity_level in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH]
        assert prediction_result.model_version is not None
    
    @pytest.mark.asyncio
    async def test_store_prediction(self, scheduler):
        """Test storing prediction results."""
        # Create test prediction result
        prediction_result = PredictionResult(
            timestamp=datetime.utcnow(),
            flare_probability=0.75,
            severity_level=SeverityLevel.HIGH,
            confidence_score=0.85,
            model_version="test-model",
            raw_output={"test": "data"},
            solar_data={"test": "solar_data"}
        )
        
        prediction_id = await scheduler.store_prediction(prediction_result)
        
        assert prediction_id == "test-prediction-id"
        scheduler.prediction_repository.create.assert_called_once_with(prediction_result)
    
    @pytest.mark.asyncio
    async def test_should_trigger_alert(self, scheduler):
        """Test alert triggering logic."""
        # Test low severity, low probability - no alert
        low_prediction = PredictionResult(
            timestamp=datetime.utcnow(),
            flare_probability=0.2,
            severity_level=SeverityLevel.LOW,
            confidence_score=0.8,
            model_version="test",
            raw_output={},
            solar_data={}
        )
        assert not scheduler._should_trigger_alert(low_prediction)
        
        # Test high severity, high probability - should alert
        high_prediction = PredictionResult(
            timestamp=datetime.utcnow(),
            flare_probability=0.9,
            severity_level=SeverityLevel.HIGH,
            confidence_score=0.8,
            model_version="test",
            raw_output={},
            solar_data={}
        )
        assert scheduler._should_trigger_alert(high_prediction)
        
        # Test medium severity, medium probability - should alert
        medium_prediction = PredictionResult(
            timestamp=datetime.utcnow(),
            flare_probability=0.65,
            severity_level=SeverityLevel.MEDIUM,
            confidence_score=0.8,
            model_version="test",
            raw_output={},
            solar_data={}
        )
        assert scheduler._should_trigger_alert(medium_prediction)
    
    @pytest.mark.asyncio
    async def test_trigger_alerts(self, scheduler):
        """Test alert triggering process."""
        # Create prediction that should trigger alert
        prediction_result = PredictionResult(
            timestamp=datetime.utcnow(),
            flare_probability=0.85,
            severity_level=SeverityLevel.HIGH,
            confidence_score=0.9,
            model_version="test",
            raw_output={},
            solar_data={}
        )
        
        # Mock the notification method
        scheduler._send_alert_notifications = AsyncMock()
        
        await scheduler.trigger_alerts(prediction_result)
        
        # Should have called notification method
        scheduler._send_alert_notifications.assert_called_once_with(prediction_result)
    
    @pytest.mark.asyncio
    async def test_execute_prediction_cycle_success(self, scheduler):
        """Test successful prediction cycle execution."""
        result = await scheduler.execute_prediction_cycle()
        
        assert isinstance(result, PredictionResult)
        assert 0.0 <= result.flare_probability <= 1.0
        
        # Verify that prediction was stored
        scheduler.prediction_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_prediction_cycle_with_retry(self, scheduler):
        """Test prediction cycle with retry logic."""
        # Make the first call fail, second succeed
        original_fetch = scheduler.fetch_solar_data
        call_count = 0
        
        async def failing_fetch():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated failure")
            return await original_fetch()
        
        scheduler.fetch_solar_data = failing_fetch
        
        result = await scheduler.execute_prediction_cycle()
        
        assert isinstance(result, PredictionResult)
        assert call_count == 2  # Should have retried once
    
    @pytest.mark.asyncio
    async def test_execute_prediction_cycle_max_retries(self, scheduler):
        """Test prediction cycle with max retries exceeded."""
        # Make all calls fail
        async def always_failing_fetch():
            raise RuntimeError("Persistent failure")
        
        scheduler.fetch_solar_data = always_failing_fetch
        
        result = await scheduler.execute_prediction_cycle()
        
        assert result is None  # Should return None after max retries
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, scheduler):
        """Test starting and stopping the scheduler."""
        assert not scheduler._running
        
        # Start scheduler
        await scheduler.start()
        assert scheduler._running
        assert scheduler._task is not None
        
        # Stop scheduler
        await scheduler.stop()
        assert not scheduler._running
    
    @pytest.mark.asyncio
    async def test_scheduler_double_start(self, scheduler):
        """Test that double start doesn't cause issues."""
        await scheduler.start()
        first_task = scheduler._task
        
        await scheduler.start()  # Should not create new task
        
        assert scheduler._task is first_task
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_scheduler_stop_without_start(self, scheduler):
        """Test stopping scheduler that wasn't started."""
        # Should not raise any exceptions
        await scheduler.stop()
        assert not scheduler._running
    
    @pytest.mark.asyncio
    async def test_get_status(self, scheduler):
        """Test getting scheduler status."""
        status = await scheduler.get_status()
        
        assert "running" in status
        assert "config" in status
        assert "status_timestamp" in status
        assert isinstance(status["running"], bool)
        assert isinstance(status["config"], dict)
    
    @pytest.mark.asyncio
    async def test_get_status_with_latest_prediction(self, scheduler):
        """Test getting status with latest prediction data."""
        # Mock a recent prediction
        mock_prediction = PredictionResult(
            timestamp=datetime.utcnow(),
            flare_probability=0.65,
            severity_level=SeverityLevel.MEDIUM,
            confidence_score=0.8,
            model_version="test",
            raw_output={},
            solar_data={}
        )
        
        scheduler.prediction_repository.get_current_prediction.return_value = mock_prediction
        
        status = await scheduler.get_status()
        
        assert status["latest_prediction"] is not None
        assert status["latest_prediction"]["flare_probability"] == 0.65
        assert status["latest_prediction"]["severity_level"] == SeverityLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_calculate_next_prediction_eta(self, scheduler):
        """Test calculating next prediction ETA."""
        # When not running, should return None
        eta = scheduler._calculate_next_prediction_eta()
        assert eta is None
        
        # When running, should return a future timestamp
        scheduler._running = True
        eta = scheduler._calculate_next_prediction_eta()
        assert eta is not None
        
        # Parse the ISO timestamp and verify it's in the future
        eta_time = datetime.fromisoformat(eta.replace('Z', '+00:00').replace('+00:00', ''))
        assert eta_time > datetime.utcnow()


class TestGlobalSchedulerFunctions:
    """Test global scheduler management functions."""
    
    @pytest.mark.asyncio
    async def test_get_prediction_scheduler_singleton(self):
        """Test that get_prediction_scheduler returns the same instance."""
        # Clean up any existing instance
        await stop_prediction_scheduler()
        
        scheduler1 = await get_prediction_scheduler()
        scheduler2 = await get_prediction_scheduler()
        
        assert scheduler1 is scheduler2
        
        # Clean up
        await stop_prediction_scheduler()
    
    @pytest.mark.asyncio
    async def test_start_stop_prediction_scheduler(self):
        """Test starting and stopping the global scheduler."""
        # Start scheduler
        await start_prediction_scheduler()
        
        scheduler = await get_prediction_scheduler()
        assert scheduler._running
        
        # Stop scheduler
        await stop_prediction_scheduler()
        
        # Getting a new instance should create a new one
        new_scheduler = await get_prediction_scheduler()
        assert new_scheduler is not scheduler
        
        # Clean up
        await stop_prediction_scheduler()


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_prediction_pipeline(self):
        """Test the complete prediction pipeline from data fetch to storage."""
        config = SchedulerConfig(
            prediction_interval_minutes=1,
            max_retries=1,
            enable_mock_data=True
        )
        
        scheduler = PredictionScheduler(config)
        
        # Mock the repository
        mock_repo = AsyncMock()
        mock_prediction = AsyncMock()
        mock_prediction.id = "integration-test-id"
        mock_repo.create = AsyncMock(return_value=mock_prediction)
        scheduler.prediction_repository = mock_repo
        
        try:
            # Execute a complete cycle
            result = await scheduler.execute_prediction_cycle()
            
            # Verify the result
            assert isinstance(result, PredictionResult)
            assert result.timestamp is not None
            assert 0.0 <= result.flare_probability <= 1.0
            assert result.severity_level in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH]
            
            # Verify storage was called
            mock_repo.create.assert_called_once()
            stored_prediction = mock_repo.create.call_args[0][0]
            assert isinstance(stored_prediction, PredictionResult)
            
        finally:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_scheduler_resilience(self):
        """Test scheduler resilience to various failure scenarios."""
        config = SchedulerConfig(
            prediction_interval_minutes=1,
            max_retries=2,
            retry_delay_seconds=0.1,  # Fast retry for testing
            enable_mock_data=True
        )
        
        scheduler = PredictionScheduler(config)
        
        # Mock repository with intermittent failures
        mock_repo = AsyncMock()
        call_count = 0
        
        async def intermittent_create(prediction):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise RuntimeError("Simulated database failure")
            return f"prediction-{call_count}"
        
        async def intermittent_create_wrapper(prediction):
            result = await intermittent_create(prediction)
            mock_result = AsyncMock()
            mock_result.id = result
            return mock_result
        
        mock_repo.create = intermittent_create_wrapper
        mock_repo.get_current_prediction = AsyncMock(return_value=None)
        scheduler.prediction_repository = mock_repo
        
        try:
            # Execute multiple cycles
            results = []
            for i in range(5):
                result = await scheduler.execute_prediction_cycle()
                results.append(result)
            
            # Some should succeed, some might fail
            successful_results = [r for r in results if r is not None]
            assert len(successful_results) > 0  # At least some should succeed
            
        finally:
            await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_scheduler_operations(self):
        """Test concurrent scheduler operations."""
        config = SchedulerConfig(enable_mock_data=True)
        scheduler = PredictionScheduler(config)
        
        # Mock repository
        mock_repo = AsyncMock()
        mock_prediction = AsyncMock()
        mock_prediction.id = "concurrent-test-id"
        mock_repo.create = AsyncMock(return_value=mock_prediction)
        mock_repo.get_current_prediction = AsyncMock(return_value=None)
        scheduler.prediction_repository = mock_repo
        
        try:
            # Start multiple concurrent operations
            tasks = [
                scheduler.execute_prediction_cycle(),
                scheduler.execute_prediction_cycle(),
                scheduler.get_status()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that operations completed without major issues
            prediction_results = [r for r in results[:2] if isinstance(r, PredictionResult)]
            status_result = results[2]
            
            assert len(prediction_results) >= 1  # At least one should succeed
            assert isinstance(status_result, dict)  # Status should work
            
        finally:
            await scheduler.stop()


if __name__ == "__main__":
    pytest.main([__file__])