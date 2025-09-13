"""Tests for logging and monitoring functionality."""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.utils.logging import (
    RequestLogger,
    ErrorTracker,
    MetricsCollector,
    setup_logging,
    get_logger
)
from app.middleware.logging import (
    RequestLoggingMiddleware,
    PerformanceMonitoringMiddleware,
    ErrorHandlingMiddleware
)
from app.api.health import router as health_router
from app.models.core import SolarData


class TestStructuredLogging:
    """Test structured logging functionality."""
    
    def test_setup_logging(self):
        """Test logging setup configuration."""
        setup_logging()
        logger = get_logger("test")
        assert logger is not None
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test.module")
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')


class TestRequestLogger:
    """Test request logging functionality."""
    
    @pytest.fixture
    def request_logger(self):
        """Create request logger instance."""
        return RequestLogger("test.requests")
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.url = Mock()
        request.url.path = "/api/v1/alerts/current"
        request.url.__str__ = Mock(return_value="http://localhost:8000/api/v1/alerts/current")
        request.query_params = {}
        request.headers = {"user-agent": "test-client", "content-type": "application/json"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        request.state.request_id = "test-request-123"
        return request
    
    @pytest.mark.asyncio
    async def test_log_successful_request(self, request_logger, mock_request):
        """Test logging successful request."""
        await request_logger.log_request(
            request=mock_request,
            response_status=200,
            response_time=0.123,
            user_id="user123"
        )
        # Test passes if no exception is raised
    
    @pytest.mark.asyncio
    async def test_log_failed_request(self, request_logger, mock_request):
        """Test logging failed request."""
        error = ValueError("Test error")
        await request_logger.log_request(
            request=mock_request,
            response_status=500,
            response_time=0.456,
            user_id="user123",
            error=error
        )
        # Test passes if no exception is raised
    
    @pytest.mark.asyncio
    async def test_log_request_without_user(self, request_logger, mock_request):
        """Test logging request without user ID."""
        await request_logger.log_request(
            request=mock_request,
            response_status=404,
            response_time=0.089
        )
        # Test passes if no exception is raised


class TestErrorTracker:
    """Test error tracking functionality."""
    
    @pytest.fixture
    def error_tracker(self):
        """Create error tracker instance."""
        return ErrorTracker("test.errors")
    
    def test_track_error(self, error_tracker):
        """Test error tracking."""
        error = RuntimeError("Test runtime error")
        context = {"operation": "test_operation", "data": {"key": "value"}}
        
        error_id = error_tracker.track_error(
            error=error,
            context=context,
            user_id="user123",
            request_id="req123",
            severity="error"
        )
        
        assert error_id is not None
        assert error_id.startswith("err_")
    
    def test_track_critical_error(self, error_tracker):
        """Test critical error tracking."""
        error = Exception("Critical system failure")
        
        error_id = error_tracker.track_error(
            error=error,
            severity="critical"
        )
        
        assert error_id is not None
    
    def test_track_performance_issue(self, error_tracker):
        """Test performance issue tracking."""
        error_tracker.track_performance_issue(
            operation="database_query",
            duration=2.5,
            threshold=1.0,
            context={"query": "SELECT * FROM predictions"}
        )
        # Test passes if no exception is raised


class TestMetricsCollector:
    """Test metrics collection functionality."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector instance."""
        return MetricsCollector("test.metrics")
    
    def test_record_prediction_metrics(self, metrics_collector):
        """Test prediction metrics recording."""
        metrics_collector.record_prediction_metrics(
            model_version="surya-1.0",
            inference_time=0.234,
            accuracy_score=0.89
        )
        # Test passes if no exception is raised
    
    def test_record_prediction_metrics_with_error(self, metrics_collector):
        """Test prediction metrics with error."""
        metrics_collector.record_prediction_metrics(
            model_version="surya-1.0",
            inference_time=1.234,
            error="Model timeout"
        )
        # Test passes if no exception is raised
    
    def test_record_api_metrics(self, metrics_collector):
        """Test API metrics recording."""
        metrics_collector.record_api_metrics(
            endpoint="/api/v1/alerts/current",
            method="GET",
            response_time=0.123,
            status_code=200,
            user_tier="pro"
        )
        # Test passes if no exception is raised
    
    def test_record_websocket_metrics(self, metrics_collector):
        """Test WebSocket metrics recording."""
        metrics_collector.record_websocket_metrics(
            event_type="connection_opened",
            connection_count=5,
            message_size=1024,
            delivery_time=0.045
        )
        # Test passes if no exception is raised
    
    def test_record_database_metrics(self, metrics_collector):
        """Test database metrics recording."""
        metrics_collector.record_database_metrics(
            operation="SELECT",
            table="predictions",
            query_time=0.067,
            rows_affected=10
        )
        # Test passes if no exception is raised
    
    def test_record_database_metrics_with_error(self, metrics_collector):
        """Test database metrics with error."""
        metrics_collector.record_database_metrics(
            operation="INSERT",
            table="predictions",
            query_time=0.234,
            error="Connection timeout"
        )
        # Test passes if no exception is raised


class TestLoggingMiddleware:
    """Test logging middleware functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with middleware."""
        app = FastAPI()
        
        # Add middleware in reverse order (last added is executed first)
        app.add_middleware(ErrorHandlingMiddleware)
        app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=0.1)
        app.add_middleware(RequestLoggingMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/test-error")
        async def test_error_endpoint():
            raise ValueError("Test error")
        
        @app.get("/test-slow")
        async def test_slow_endpoint():
            await asyncio.sleep(0.2)  # Slower than threshold
            return {"message": "slow"}
        
        return app
    
    def test_request_logging_middleware(self, app):
        """Test request logging middleware."""
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers
    
    def test_error_handling_middleware(self, app):
        """Test error handling middleware."""
        client = TestClient(app)
        response = client.get("/test-error")
        
        assert response.status_code == 400  # ValueError mapped to 400
        data = response.json()
        assert "error_code" in data
        assert "message" in data
        assert "request_id" in data
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_performance_monitoring_middleware(self, app):
        """Test performance monitoring middleware."""
        client = TestClient(app)
        response = client.get("/test-slow")
        
        assert response.status_code == 200
        # Performance issue should be logged (but we can't easily test the log output)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test app with health endpoints."""
        app = FastAPI()
        app.include_router(health_router)
        return app
    
    def test_basic_health_check(self, app):
        """Test basic health check endpoint."""
        client = TestClient(app)
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data
    
    @patch('app.api.health.get_database')
    @patch('app.services.model_inference.ModelInferenceService')
    def test_detailed_health_check(self, mock_model_service, mock_db, app):
        """Test detailed health check endpoint."""
        # Mock database
        mock_db_instance = AsyncMock()
        mock_db_instance.fetch_one = AsyncMock(return_value={"test": 1})
        mock_db.return_value = mock_db_instance
        
        # Mock model service
        mock_model_instance = AsyncMock()
        mock_model_instance.check_model_health = AsyncMock(return_value=True)
        mock_model_service.return_value = mock_model_instance
        
        client = TestClient(app)
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "system_metrics" in data
    
    def test_readiness_check(self, app):
        """Test readiness probe endpoint."""
        with patch('app.api.health.get_database') as mock_db, \
             patch('app.services.model_inference.ModelInferenceService') as mock_model_service:
            
            # Mock successful checks
            mock_db_instance = AsyncMock()
            mock_db_instance.fetch_one = AsyncMock(return_value={"test": 1})
            mock_db.return_value = mock_db_instance
            
            mock_model_instance = AsyncMock()
            mock_model_instance.check_model_health = AsyncMock(return_value=True)
            mock_model_service.return_value = mock_model_instance
            
            client = TestClient(app)
            response = client.get("/health/readiness")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
    
    def test_liveness_check(self, app):
        """Test liveness probe endpoint."""
        client = TestClient(app)
        response = client.get("/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    def test_system_metrics(self, app):
        """Test system metrics endpoint."""
        client = TestClient(app)
        response = client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "process" in data
        assert "timestamp" in data


class TestErrorScenarios:
    """Test various error scenarios and their handling."""
    
    @pytest.fixture
    def error_tracker(self):
        """Create error tracker for testing."""
        return ErrorTracker("test.error_scenarios")
    
    def test_handle_validation_error(self, error_tracker):
        """Test handling of validation errors."""
        error = ValueError("Invalid input data")
        error_id = error_tracker.track_error(error, severity="warning")
        assert error_id is not None
    
    def test_handle_connection_error(self, error_tracker):
        """Test handling of connection errors."""
        error = ConnectionError("Database connection failed")
        error_id = error_tracker.track_error(error, severity="error")
        assert error_id is not None
    
    def test_handle_timeout_error(self, error_tracker):
        """Test handling of timeout errors."""
        error = TimeoutError("Request timed out")
        error_id = error_tracker.track_error(error, severity="error")
        assert error_id is not None
    
    def test_handle_permission_error(self, error_tracker):
        """Test handling of permission errors."""
        error = PermissionError("Access denied")
        error_id = error_tracker.track_error(error, severity="warning")
        assert error_id is not None


class TestPerformanceMetrics:
    """Test performance metrics collection."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector for testing."""
        return MetricsCollector("test.performance")
    
    def test_model_inference_metrics(self, metrics_collector):
        """Test model inference performance metrics."""
        # Successful prediction
        metrics_collector.record_prediction_metrics(
            model_version="surya-1.0",
            inference_time=0.456,
            accuracy_score=0.92
        )
        
        # Failed prediction
        metrics_collector.record_prediction_metrics(
            model_version="surya-1.0",
            inference_time=2.1,
            error="Model timeout"
        )
    
    def test_api_performance_metrics(self, metrics_collector):
        """Test API performance metrics."""
        # Fast request
        metrics_collector.record_api_metrics(
            endpoint="/api/v1/alerts/current",
            method="GET",
            response_time=0.089,
            status_code=200,
            user_tier="enterprise"
        )
        
        # Slow request
        metrics_collector.record_api_metrics(
            endpoint="/api/v1/alerts/history",
            method="GET",
            response_time=1.234,
            status_code=200,
            user_tier="free"
        )
    
    def test_websocket_performance_metrics(self, metrics_collector):
        """Test WebSocket performance metrics."""
        # Connection events
        metrics_collector.record_websocket_metrics(
            event_type="connection_opened",
            connection_count=10
        )
        
        # Message delivery
        metrics_collector.record_websocket_metrics(
            event_type="message_sent",
            connection_count=10,
            message_size=512,
            delivery_time=0.023
        )
    
    def test_database_performance_metrics(self, metrics_collector):
        """Test database performance metrics."""
        # Fast query
        metrics_collector.record_database_metrics(
            operation="SELECT",
            table="predictions",
            query_time=0.034,
            rows_affected=5
        )
        
        # Slow query
        metrics_collector.record_database_metrics(
            operation="SELECT",
            table="predictions",
            query_time=0.567,
            rows_affected=1000
        )
        
        # Failed query
        metrics_collector.record_database_metrics(
            operation="INSERT",
            table="predictions",
            query_time=0.123,
            error="Constraint violation"
        )


if __name__ == "__main__":
    pytest.main([__file__])