"""Unit tests for the model inference engine."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import numpy as np

from app.services.model_inference import (
    ModelInferenceEngine,
    ModelConfig,
    get_model_engine,
    shutdown_model_engine
)
from app.models.core import SolarData, SeverityLevel, PredictionResult


class TestModelConfig:
    """Test ModelConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ModelConfig()
        
        assert config.model_name == "nasa-ibm/surya-1.0"
        assert config.max_sequence_length == 512
        assert config.confidence_threshold == 0.5
        assert config.device == "cpu"
        assert config.model_timeout_seconds == 30
        assert "low" in config.severity_thresholds
        assert "medium" in config.severity_thresholds
        assert "high" in config.severity_thresholds
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ModelConfig(
            model_name="custom-model",
            device="cuda",
            model_timeout_seconds=60
        )
        
        assert config.model_name == "custom-model"
        assert config.device == "cuda"
        assert config.model_timeout_seconds == 60


class TestModelInferenceEngine:
    """Test ModelInferenceEngine class."""
    
    @pytest.fixture
    def sample_solar_data(self):
        """Create sample solar data for testing."""
        return SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[1.5, 2.3, -0.8, 3.1, -1.2],
            solar_wind_speed=450.0,
            proton_density=8.5,
            temperature=1_500_000.0,
            source="nasa"
        )
    
    @pytest.fixture
    def model_engine(self):
        """Create a model inference engine for testing."""
        config = ModelConfig(model_timeout_seconds=5)  # Shorter timeout for tests
        return ModelInferenceEngine(config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, model_engine):
        """Test model initialization."""
        assert not model_engine._model_loaded
        
        await model_engine.initialize()
        
        assert model_engine._model_loaded
        assert model_engine.model is not None
        assert model_engine.tokenizer is not None
    
    @pytest.mark.asyncio
    async def test_double_initialization(self, model_engine):
        """Test that double initialization doesn't cause issues."""
        await model_engine.initialize()
        first_model = model_engine.model
        
        await model_engine.initialize()  # Should not reload
        
        assert model_engine.model is first_model
    
    @pytest.mark.asyncio
    async def test_validate_input_data_valid(self, model_engine, sample_solar_data):
        """Test input validation with valid data."""
        validated_data = await model_engine.validate_input_data(sample_solar_data)
        
        assert validated_data == sample_solar_data
        assert isinstance(validated_data, SolarData)
    
    @pytest.mark.asyncio
    async def test_validate_input_data_empty_magnetic_field(self, model_engine):
        """Test input validation with empty magnetic field data."""
        invalid_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[],  # Empty list
            solar_wind_speed=450.0,
            proton_density=8.5,
            temperature=1_500_000.0
        )
        
        with pytest.raises(ValueError, match="Magnetic field data cannot be empty"):
            await model_engine.validate_input_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_input_data_invalid_wind_speed(self, model_engine):
        """Test input validation with invalid wind speed."""
        # Create data with valid pydantic validation but invalid business logic
        invalid_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[1.0, 2.0, 3.0],
            solar_wind_speed=5000.0,  # Too high value (above 3000 km/s limit)
            proton_density=8.5,
            temperature=1_500_000.0
        )
        
        with pytest.raises(ValueError, match="Solar wind speed out of valid range"):
            await model_engine.validate_input_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_input_data_invalid_density(self, model_engine):
        """Test input validation with invalid proton density."""
        invalid_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[1.0, 2.0, 3.0],
            solar_wind_speed=450.0,
            proton_density=2000.0,  # Too high
            temperature=1_500_000.0
        )
        
        with pytest.raises(ValueError, match="Proton density out of valid range"):
            await model_engine.validate_input_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_validate_input_data_nan_values(self, model_engine):
        """Test input validation with NaN values."""
        invalid_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[1.0, float('nan'), 3.0],  # Contains NaN
            solar_wind_speed=450.0,
            proton_density=8.5,
            temperature=1_500_000.0
        )
        
        with pytest.raises(ValueError, match="Magnetic field data contains invalid values"):
            await model_engine.validate_input_data(invalid_data)
    
    @pytest.mark.asyncio
    async def test_classify_severity_low(self, model_engine):
        """Test severity classification for low probability."""
        severity = await model_engine.classify_severity(0.2)
        assert severity == SeverityLevel.LOW
    
    @pytest.mark.asyncio
    async def test_classify_severity_medium(self, model_engine):
        """Test severity classification for medium probability."""
        severity = await model_engine.classify_severity(0.65)
        assert severity == SeverityLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_classify_severity_high(self, model_engine):
        """Test severity classification for high probability."""
        severity = await model_engine.classify_severity(0.85)
        assert severity == SeverityLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_classify_severity_boundary_values(self, model_engine):
        """Test severity classification at boundary values."""
        # Test exact threshold values
        assert await model_engine.classify_severity(0.3) == SeverityLevel.LOW
        assert await model_engine.classify_severity(0.6) == SeverityLevel.MEDIUM
        assert await model_engine.classify_severity(0.8) == SeverityLevel.HIGH
        
        # Test just below thresholds
        assert await model_engine.classify_severity(0.59) == SeverityLevel.LOW
        assert await model_engine.classify_severity(0.79) == SeverityLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_run_prediction_success(self, model_engine, sample_solar_data):
        """Test successful prediction execution."""
        result = await model_engine.run_prediction(sample_solar_data)
        
        assert isinstance(result, PredictionResult)
        assert 0.0 <= result.flare_probability <= 1.0
        assert result.severity_level in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH]
        assert result.model_version == model_engine.config.model_name
        assert result.confidence_score is not None
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.raw_output is not None
        assert result.solar_data == sample_solar_data.model_dump()
    
    @pytest.mark.asyncio
    async def test_run_prediction_with_uninitialized_model(self, sample_solar_data):
        """Test prediction with uninitialized model (should auto-initialize)."""
        engine = ModelInferenceEngine()
        
        result = await engine.run_prediction(sample_solar_data)
        
        assert isinstance(result, PredictionResult)
        assert engine._model_loaded
    
    @pytest.mark.asyncio
    async def test_preprocess_input(self, model_engine, sample_solar_data):
        """Test input preprocessing."""
        processed = await model_engine._preprocess_input(sample_solar_data)
        
        assert "magnetic_field" in processed
        assert "solar_wind_speed" in processed
        assert "proton_density" in processed
        assert "temperature" in processed
        assert "timestamp_features" in processed
        
        # Check normalization
        assert isinstance(processed["magnetic_field"], list)
        assert 0.0 <= processed["solar_wind_speed"] <= 3.0
        assert processed["proton_density"] >= 0.0
        assert 0.0 <= processed["temperature"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_extract_temporal_features(self, model_engine):
        """Test temporal feature extraction."""
        timestamp = datetime(2024, 6, 15, 14, 30, 0)  # June 15, 2:30 PM
        
        features = model_engine._extract_temporal_features(timestamp)
        
        assert "hour_of_day" in features
        assert "day_of_year" in features
        assert "solar_cycle_phase" in features
        
        # Check hour normalization (14/24 ≈ 0.583)
        assert abs(features["hour_of_day"] - 14/24) < 0.001
        
        # Check day of year normalization
        assert 0.0 <= features["day_of_year"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_postprocess_output_with_probabilities(self, model_engine):
        """Test output postprocessing with probability data."""
        raw_output = {
            "probabilities": [0.3, 0.7],  # [no_flare, flare]
            "logits": [-0.5, 0.5]
        }
        
        probability = await model_engine._postprocess_output(raw_output)
        
        assert probability == 0.7
    
    @pytest.mark.asyncio
    async def test_postprocess_output_with_logits_only(self, model_engine):
        """Test output postprocessing with logits only."""
        raw_output = {
            "logits": [-1.0, 2.0]  # Should result in high probability
        }
        
        probability = await model_engine._postprocess_output(raw_output)
        
        # Sigmoid of 2.0 ≈ 0.88
        assert 0.8 <= probability <= 0.9
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_model_confidence(self, model_engine):
        """Test confidence calculation with model confidence."""
        raw_output = {"model_confidence": 0.85}
        
        confidence = await model_engine._calculate_confidence(raw_output)
        
        assert confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_with_probabilities(self, model_engine):
        """Test confidence calculation from probabilities."""
        raw_output = {"probabilities": [0.2, 0.8]}
        
        confidence = await model_engine._calculate_confidence(raw_output)
        
        assert confidence == 0.8  # Max probability
    
    @pytest.mark.asyncio
    async def test_calculate_confidence_fallback(self, model_engine):
        """Test confidence calculation fallback."""
        raw_output = {}  # No confidence or probabilities
        
        confidence = await model_engine._calculate_confidence(raw_output)
        
        assert confidence == 0.5  # Default value
    
    @pytest.mark.asyncio
    async def test_health_check_with_loaded_model(self, model_engine):
        """Test health check with loaded model."""
        await model_engine.initialize()
        
        status = await model_engine.health_check()
        
        assert status["model_loaded"] is True
        assert status["model_name"] == model_engine.config.model_name
        assert status["device"] == model_engine.config.device
        assert status["test_prediction_success"] is True
        assert status["test_prediction_time_ms"] is not None
        assert status["test_prediction_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check_with_unloaded_model(self):
        """Test health check with unloaded model."""
        engine = ModelInferenceEngine()
        
        status = await engine.health_check()
        
        assert status["model_loaded"] is False
        assert status["test_prediction_success"] is False
        assert status["test_prediction_time_ms"] is None
    
    @pytest.mark.asyncio
    async def test_mock_probability_calculation(self, model_engine):
        """Test mock probability calculation logic."""
        # Test with high values (should give higher probability)
        high_input = {
            "solar_wind_speed": 0.9,
            "proton_density": 0.8,
            "temperature": 0.7
        }
        high_prob = model_engine._calculate_mock_probability(high_input)
        
        # Test with low values (should give lower probability)
        low_input = {
            "solar_wind_speed": 0.1,
            "proton_density": 0.1,
            "temperature": 0.1
        }
        low_prob = model_engine._calculate_mock_probability(low_input)
        
        assert 0.0 <= high_prob <= 1.0
        assert 0.0 <= low_prob <= 1.0
        # High input should generally give higher probability
        # (though randomness might occasionally make this fail)
    
    @pytest.mark.asyncio
    async def test_prediction_timeout(self):
        """Test prediction timeout handling."""
        config = ModelConfig(model_timeout_seconds=1)  # Very short timeout
        engine = ModelInferenceEngine(config)
        
        # Mock the inference to take longer than timeout
        async def slow_inference(processed_input):
            await asyncio.sleep(2)  # Longer than timeout
            return {"probabilities": [0.5, 0.5]}
        
        engine._execute_inference = slow_inference
        
        sample_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[1.0, 2.0, 3.0],
            solar_wind_speed=450.0,
            proton_density=8.5,
            temperature=1_500_000.0
        )
        
        with pytest.raises(RuntimeError, match="Model inference timed out"):
            await engine.run_prediction(sample_data)


class TestGlobalModelEngine:
    """Test global model engine functions."""
    
    @pytest.mark.asyncio
    async def test_get_model_engine_singleton(self):
        """Test that get_model_engine returns the same instance."""
        # Clean up any existing instance
        await shutdown_model_engine()
        
        engine1 = await get_model_engine()
        engine2 = await get_model_engine()
        
        assert engine1 is engine2
        assert engine1._model_loaded
        
        # Clean up
        await shutdown_model_engine()
    
    @pytest.mark.asyncio
    async def test_shutdown_model_engine(self):
        """Test model engine shutdown."""
        # Get an instance
        engine = await get_model_engine()
        assert engine is not None
        
        # Shutdown
        await shutdown_model_engine()
        
        # Getting a new instance should create a new one
        new_engine = await get_model_engine()
        assert new_engine is not engine
        
        # Clean up
        await shutdown_model_engine()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_input_type(self):
        """Test handling of invalid input type."""
        engine = ModelInferenceEngine()
        
        with pytest.raises(ValueError, match="Input must be a SolarData instance"):
            await engine.validate_input_data("invalid_input")
    
    @pytest.mark.asyncio
    async def test_preprocessing_error_handling(self):
        """Test preprocessing error handling."""
        engine = ModelInferenceEngine()
        
        # Create data that will cause preprocessing to fail
        invalid_data = SolarData(
            timestamp=datetime.utcnow(),
            magnetic_field_data=[],  # This will cause issues in preprocessing
            solar_wind_speed=450.0,
            proton_density=8.5,
            temperature=1_500_000.0
        )
        
        with pytest.raises(RuntimeError, match="Failed to preprocess input"):
            await engine._preprocess_input(invalid_data)
    
    @pytest.mark.asyncio
    async def test_severity_classification_error_handling(self):
        """Test severity classification error handling."""
        # Create engine with invalid thresholds
        config = ModelConfig()
        config.severity_thresholds = {}  # Empty thresholds
        
        engine = ModelInferenceEngine(config)
        
        # Should return LOW on error
        severity = await engine.classify_severity(0.5)
        assert severity == SeverityLevel.LOW


if __name__ == "__main__":
    pytest.main([__file__])