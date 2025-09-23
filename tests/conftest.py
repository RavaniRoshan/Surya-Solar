"""
Pytest configuration and shared fixtures for the test suite.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import shutil

# Set test environment - must be done before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["SUPABASE_URL"] = "http://localhost:54321"
os.environ["SUPABASE_ANON_KEY"] = "test_key"
os.environ["SUPABASE_SERVICE_KEY"] = "test_service_key"
os.environ["RAZORPAY_KEY_ID"] = "test_razorpay_key"
os.environ["RAZORPAY_KEY_SECRET"] = "test_razorpay_secret"
os.environ["HUGGINGFACE_API_TOKEN"] = "test_hf_token"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_for_testing_only"
os.environ["JWT_ALGORITHM"] = "HS256"

from app.main import app
from app.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    settings = get_settings()
    settings.environment = "test"
    settings.database_url = "postgresql://test:test@localhost:5432/test_db"
    settings.supabase_url = "http://localhost:54321"
    settings.supabase_anon_key = "test_key"
    return settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()
    mock_client.auth = MagicMock()
    mock_client.table = MagicMock()
    mock_client.storage = MagicMock()
    return mock_client


@pytest.fixture
def mock_model_client():
    """Mock ML model client for testing."""
    mock_client = AsyncMock()
    mock_client.run_inference = AsyncMock(return_value={
        "flare_probability": 0.75,
        "confidence_score": 0.85,
        "raw_output": {"prediction": [0.75]}
    })
    return mock_client


@pytest.fixture
def mock_razorpay_client():
    """Mock Razorpay client for testing."""
    mock_client = MagicMock()
    mock_client.subscription = MagicMock()
    mock_client.payment_link = MagicMock()
    mock_client.webhook = MagicMock()
    return mock_client


@pytest.fixture
def sample_prediction_data():
    """Sample prediction data for testing."""
    return {
        "timestamp": "2024-01-01T12:00:00Z",
        "flare_probability": 0.75,
        "severity_level": "high",
        "confidence_score": 0.85,
        "model_version": "surya-1.0",
        "raw_output": {"prediction": [0.75]}
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "subscription_tier": "pro",
        "api_key": "test-api-key",
        "webhook_url": "https://example.com/webhook"
    }


@pytest.fixture
def sample_solar_data():
    """Sample solar data for testing."""
    return {
        "timestamp": "2024-01-01T12:00:00Z",
        "magnetic_field_data": [1.0, 2.0, 3.0],
        "solar_wind_speed": 400.0,
        "proton_density": 5.0,
        "temperature": 100000.0,
        "source": "nasa"
    }


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.receive_json = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


# Performance test fixtures
@pytest.fixture
def performance_test_data():
    """Generate data for performance testing."""
    return {
        "concurrent_users": 100,
        "requests_per_user": 10,
        "test_duration": 30,  # seconds
        "acceptable_response_time": 0.2,  # 200ms
        "acceptable_error_rate": 0.01  # 1%
    }


# Database fixtures
@pytest.fixture
async def clean_database():
    """Clean database before and after tests."""
    # This would typically clean test database tables
    # For now, we'll use mocks
    yield
    # Cleanup after test


# Authentication fixtures
@pytest.fixture
def auth_headers():
    """Generate authentication headers for testing."""
    return {
        "Authorization": "Bearer test-jwt-token",
        "X-API-Key": "test-api-key"
    }


@pytest.fixture
def invalid_auth_headers():
    """Generate invalid authentication headers for testing."""
    return {
        "Authorization": "Bearer invalid-token",
        "X-API-Key": "invalid-key"
    }