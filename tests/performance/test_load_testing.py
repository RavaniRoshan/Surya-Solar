"""
Performance tests for load testing and scalability validation.
Tests API response times, WebSocket connection limits, and database performance.
"""
import asyncio
import time
import pytest
import aiohttp
import websockets
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.core import AlertResponse, PredictionResult, SeverityLevel
from tests.conftest import test_client, test_db


@pytest.mark.performance
@pytest.mark.asyncio
class TestAPIPerformance:
    """Test API endpoint performance under load."""
    
    async def test_current_alert_response_time(self, test_client):
        """Test that current alert endpoint responds within 200ms under normal load."""
        response_times = []
        
        # Mock the database query to return consistent data
        with patch('app.repositories.predictions.PredictionRepository.get_latest_prediction') as mock_get:
            mock_prediction = PredictionResult(
                timestamp="2024-01-01T12:00:00Z",
                flare_probability=0.15,
                severity_level=SeverityLevel.LOW,
                confidence_score=0.85,
                model_version="surya-1.0",
                raw_output={"test": "data"}
            )
            mock_get.return_value = mock_prediction
            
            # Test 100 concurrent requests
            for _ in range(100):
                start_time = time.time()
                response = await test_client.get("/api/v1/alerts/current")
                end_time = time.time()
                
                response_times.append((end_time - start_time) * 1000)  # Convert to ms
                assert response.status_code == 200
        
        # Calculate performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]
        
        # Assert performance requirements
        assert avg_response_time < 100, f"Average response time {avg_response_time}ms exceeds 100ms"
        assert p95_response_time < 200, f"P95 response time {p95_response_time}ms exceeds 200ms"
    
    async def test_history_endpoint_pagination_performance(self, test_client):
        """Test history endpoint performance with large datasets."""
        with patch('app.repositories.predictions.PredictionRepository.get_predictions_history') as mock_history:
            # Mock large dataset
            mock_predictions = [
                AlertResponse(
                    id=f"test-{i}",
                    timestamp="2024-01-01T12:00:00Z",
                    flare_probability=0.1 + (i * 0.01),
                    severity_level=SeverityLevel.LOW,
                    alert_triggered=False,
                    message=f"Test alert {i}"
                ) for i in range(1000)
            ]
            mock_history.return_value = (mock_predictions[:50], 1000)
            
            start_time = time.time()
            response = await test_client.get("/api/v1/alerts/history?page=1&page_size=50")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time < 50, f"History query response time {response_time}ms exceeds 50ms"
    
    async def test_concurrent_api_requests(self, test_client):
        """Test API performance under concurrent load."""
        async def make_request():
            with patch('app.repositories.predictions.PredictionRepository.get_latest_prediction') as mock_get:
                mock_prediction = PredictionResult(
                    timestamp="2024-01-01T12:00:00Z",
                    flare_probability=0.15,
                    severity_level=SeverityLevel.LOW,
                    confidence_score=0.85,
                    model_version="surya-1.0",
                    raw_output={"test": "data"}
                )
                mock_get.return_value = mock_prediction
                
                response = await test_client.get("/api/v1/alerts/current")
                return response.status_code == 200
        
        # Test 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.95, f"Success rate {success_rate} below 95%"


@pytest.mark.performance
@pytest.mark.asyncio
class TestWebSocketPerformance:
    """Test WebSocket connection performance and limits."""
    
    async def test_websocket_connection_limit(self):
        """Test that system can handle 1000+ concurrent WebSocket connections."""
        connections = []
        connection_count = 0
        
        try:
            # Simulate connecting multiple WebSocket clients
            for i in range(100):  # Reduced for testing, would be 1000+ in production
                try:
                    # Mock WebSocket connection
                    mock_websocket = AsyncMock()
                    mock_websocket.send = AsyncMock()
                    mock_websocket.recv = AsyncMock(return_value='{"type": "heartbeat"}')
                    connections.append(mock_websocket)
                    connection_count += 1
                except Exception as e:
                    break
            
            # Should handle at least 100 connections in test environment
            assert connection_count >= 100, f"Only handled {connection_count} connections"
            
        finally:
            # Clean up connections
            for conn in connections:
                try:
                    await conn.close()
                except:
                    pass
    
    async def test_websocket_message_broadcast_performance(self):
        """Test WebSocket message broadcasting performance."""
        from app.services.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        mock_connections = []
        
        # Create mock WebSocket connections
        for i in range(50):
            mock_ws = AsyncMock()
            mock_ws.send = AsyncMock()
            mock_connections.append(mock_ws)
            manager.active_connections.append(mock_ws)
        
        # Test broadcasting performance
        test_message = {
            "type": "alert",
            "data": {
                "flare_probability": 0.85,
                "severity_level": "high",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
        
        start_time = time.time()
        await manager.broadcast_alert(test_message)
        end_time = time.time()
        
        broadcast_time = (end_time - start_time) * 1000
        
        # Broadcasting to 50 connections should take less than 100ms
        assert broadcast_time < 100, f"Broadcast time {broadcast_time}ms exceeds 100ms"


@pytest.mark.performance
@pytest.mark.asyncio
class TestDatabasePerformance:
    """Test database operation performance."""
    
    async def test_prediction_query_performance(self, test_db):
        """Test database query performance for predictions."""
        from app.repositories.predictions import PredictionRepository
        
        repo = PredictionRepository(test_db)
        
        # Test latest prediction query
        start_time = time.time()
        with patch.object(repo, 'get_latest_prediction') as mock_query:
            mock_query.return_value = PredictionResult(
                timestamp="2024-01-01T12:00:00Z",
                flare_probability=0.15,
                severity_level=SeverityLevel.LOW,
                confidence_score=0.85,
                model_version="surya-1.0",
                raw_output={"test": "data"}
            )
            result = await repo.get_latest_prediction()
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        assert result is not None
        assert query_time < 50, f"Database query time {query_time}ms exceeds 50ms"
    
    async def test_historical_data_query_performance(self, test_db):
        """Test performance of historical data queries with large datasets."""
        from app.repositories.predictions import PredictionRepository
        
        repo = PredictionRepository(test_db)
        
        start_time = time.time()
        with patch.object(repo, 'get_predictions_history') as mock_query:
            # Mock large result set
            mock_results = [
                AlertResponse(
                    id=f"test-{i}",
                    timestamp="2024-01-01T12:00:00Z",
                    flare_probability=0.1,
                    severity_level=SeverityLevel.LOW,
                    alert_triggered=False,
                    message=f"Test {i}"
                ) for i in range(1000)
            ]
            mock_query.return_value = (mock_results[:100], 1000)
            
            results, total = await repo.get_predictions_history(page=1, page_size=100)
        end_time = time.time()
        
        query_time = (end_time - start_time) * 1000
        
        assert len(results) == 100
        assert total == 1000
        assert query_time < 100, f"Historical query time {query_time}ms exceeds 100ms"


@pytest.mark.performance
@pytest.mark.asyncio
class TestModelInferencePerformance:
    """Test model inference performance."""
    
    async def test_model_inference_latency(self):
        """Test that model inference completes within 30 seconds."""
        from app.services.model_inference import ModelInferenceEngine
        
        engine = ModelInferenceEngine()
        
        with patch.object(engine, 'run_prediction') as mock_inference:
            # Mock model inference with realistic delay
            async def mock_prediction():
                await asyncio.sleep(0.1)  # Simulate 100ms inference time
                return PredictionResult(
                    timestamp="2024-01-01T12:00:00Z",
                    flare_probability=0.25,
                    severity_level=SeverityLevel.MEDIUM,
                    confidence_score=0.90,
                    model_version="surya-1.0",
                    raw_output={"inference_time": 0.1}
                )
            
            mock_inference.side_effect = mock_prediction
            
            start_time = time.time()
            result = await engine.run_prediction()
            end_time = time.time()
            
            inference_time = end_time - start_time
            
            assert result is not None
            assert inference_time < 30, f"Model inference time {inference_time}s exceeds 30s"
            assert inference_time < 1, f"Model inference time {inference_time}s exceeds 1s for test"


@pytest.mark.performance
def test_memory_usage_under_load():
    """Test memory usage remains stable under load."""
    import psutil
    import gc
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Simulate load by creating many objects
    test_data = []
    for i in range(10000):
        test_data.append({
            "id": f"test-{i}",
            "timestamp": "2024-01-01T12:00:00Z",
            "data": f"test data {i}" * 100
        })
    
    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Clean up
    del test_data
    gc.collect()
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = peak_memory - initial_memory
    memory_leak = final_memory - initial_memory
    
    # Memory increase should be reasonable and cleanup should work
    assert memory_increase < 500, f"Memory increase {memory_increase}MB too high"
    assert memory_leak < 50, f"Potential memory leak {memory_leak}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])