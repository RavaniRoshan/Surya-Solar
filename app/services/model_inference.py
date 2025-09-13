"""Model inference engine for Surya-1.0 solar flare predictions."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pydantic import BaseModel, ValidationError

from app.models.core import SolarData, PredictionResult, SeverityLevel


logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """Configuration for the Surya-1.0 model."""
    model_name: str = "nasa-ibm/surya-1.0"  # Placeholder - actual model path
    max_sequence_length: int = 512
    confidence_threshold: float = 0.5
    severity_thresholds: Dict[str, float] = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.8
    }
    device: str = "cpu"  # Use CPU for now, can be changed to "cuda" if GPU available
    model_timeout_seconds: int = 30


class ModelInferenceEngine:
    """
    Handles Surya-1.0 model inference for solar flare predictions.
    
    This engine manages model loading, input preprocessing, prediction execution,
    and output postprocessing with proper error handling and validation.
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        """Initialize the model inference engine."""
        self.config = config or ModelConfig()
        self.model = None
        self.tokenizer = None
        self._model_loaded = False
        self._loading_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize and load the model asynchronously."""
        async with self._loading_lock:
            if self._model_loaded:
                return
            
            try:
                logger.info(f"Loading Surya-1.0 model: {self.config.model_name}")
                
                # For now, we'll use a mock model since the actual Surya-1.0 might not be publicly available
                # In production, this would load the actual model
                await self._load_mock_model()
                
                self._model_loaded = True
                logger.info("Model loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise RuntimeError(f"Model initialization failed: {e}")
    
    async def _load_mock_model(self) -> None:
        """Load a mock model for development purposes."""
        # In a real implementation, this would be:
        # self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        # self.model = AutoModelForSequenceClassification.from_pretrained(self.config.model_name)
        
        # For now, we'll simulate model loading
        await asyncio.sleep(0.1)  # Simulate loading time
        self.model = "mock_model"  # Placeholder
        self.tokenizer = "mock_tokenizer"  # Placeholder
    
    async def run_prediction(self, solar_data: SolarData) -> PredictionResult:
        """
        Execute a solar flare prediction using the Surya-1.0 model.
        
        Args:
            solar_data: Input solar weather data
            
        Returns:
            PredictionResult with probability, severity, and metadata
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If model inference fails
        """
        if not self._model_loaded:
            await self.initialize()
        
        try:
            # Validate input data
            validated_data = await self.validate_input_data(solar_data)
            
            # Preprocess input
            processed_input = await self._preprocess_input(validated_data)
            
            # Run inference with timeout
            raw_output = await asyncio.wait_for(
                self._execute_inference(processed_input),
                timeout=self.config.model_timeout_seconds
            )
            
            # Postprocess output
            probability = await self._postprocess_output(raw_output)
            
            # Classify severity
            severity = await self.classify_severity(probability)
            
            # Calculate confidence score
            confidence = await self._calculate_confidence(raw_output)
            
            return PredictionResult(
                timestamp=datetime.utcnow(),
                flare_probability=probability,
                severity_level=severity,
                confidence_score=confidence,
                model_version=self.config.model_name,
                raw_output=raw_output,
                solar_data=solar_data.model_dump()
            )
            
        except asyncio.TimeoutError:
            logger.error("Model inference timed out")
            raise RuntimeError("Model inference timed out")
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Prediction execution failed: {e}")
    
    async def validate_input_data(self, solar_data: SolarData) -> SolarData:
        """
        Validate and sanitize input solar data.
        
        Args:
            solar_data: Raw solar data input
            
        Returns:
            Validated solar data
            
        Raises:
            ValueError: If data validation fails
        """
        try:
            # Validate basic structure
            if not isinstance(solar_data, SolarData):
                raise ValueError("Input must be a SolarData instance")
            
            # Validate magnetic field data
            if not solar_data.magnetic_field_data:
                raise ValueError("Magnetic field data cannot be empty")
            
            if len(solar_data.magnetic_field_data) > 1000:  # Reasonable limit
                raise ValueError("Magnetic field data too large")
            
            # Validate numeric ranges
            if not (0 <= solar_data.solar_wind_speed <= 3000):  # km/s
                raise ValueError("Solar wind speed out of valid range (0-3000 km/s)")
            
            if not (0 <= solar_data.proton_density <= 1000):  # particles/cm³
                raise ValueError("Proton density out of valid range (0-1000 particles/cm³)")
            
            if not (0 <= solar_data.temperature <= 10_000_000):  # Kelvin
                raise ValueError("Temperature out of valid range (0-10M Kelvin)")
            
            # Check for NaN or infinite values
            for value in solar_data.magnetic_field_data:
                if not np.isfinite(value):
                    raise ValueError("Magnetic field data contains invalid values")
            
            logger.debug("Input data validation successful")
            return solar_data
            
        except ValidationError as e:
            logger.error(f"Data validation failed: {e}")
            raise ValueError(f"Invalid input data: {e}")
    
    async def _preprocess_input(self, solar_data: SolarData) -> Dict[str, Any]:
        """
        Preprocess solar data for model input.
        
        Args:
            solar_data: Validated solar data
            
        Returns:
            Preprocessed data ready for model inference
        """
        try:
            # Normalize magnetic field data
            mag_field_array = np.array(solar_data.magnetic_field_data)
            if len(mag_field_array) == 0:
                raise ValueError("Cannot preprocess empty magnetic field data")
            
            mag_field_normalized = (mag_field_array - np.mean(mag_field_array)) / (np.std(mag_field_array) + 1e-8)
            
            # Normalize other parameters
            wind_speed_norm = solar_data.solar_wind_speed / 1000.0  # Normalize to 0-3 range
            density_norm = solar_data.proton_density / 100.0  # Normalize to 0-10 range
            temp_norm = np.log10(solar_data.temperature + 1) / 7.0  # Log normalize temperature
            
            # Create feature vector
            features = {
                "magnetic_field": mag_field_normalized.tolist(),
                "solar_wind_speed": wind_speed_norm,
                "proton_density": density_norm,
                "temperature": temp_norm,
                "timestamp_features": self._extract_temporal_features(solar_data.timestamp)
            }
            
            logger.debug("Input preprocessing completed")
            return features
            
        except Exception as e:
            logger.error(f"Input preprocessing failed: {e}")
            raise RuntimeError(f"Failed to preprocess input: {e}")
    
    def _extract_temporal_features(self, timestamp: datetime) -> Dict[str, float]:
        """Extract temporal features from timestamp."""
        return {
            "hour_of_day": timestamp.hour / 24.0,
            "day_of_year": timestamp.timetuple().tm_yday / 365.0,
            "solar_cycle_phase": 0.5  # Placeholder for solar cycle phase
        }
    
    async def _execute_inference(self, processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute model inference on preprocessed input.
        
        Args:
            processed_input: Preprocessed input features
            
        Returns:
            Raw model output
        """
        try:
            # In a real implementation, this would use the actual model:
            # inputs = self.tokenizer(processed_input, return_tensors="pt", truncation=True, padding=True)
            # with torch.no_grad():
            #     outputs = self.model(**inputs)
            #     logits = outputs.logits
            #     probabilities = torch.softmax(logits, dim=-1)
            
            # For now, simulate model inference with realistic output
            await asyncio.sleep(0.1)  # Simulate inference time
            
            # Generate mock prediction based on input features
            base_probability = self._calculate_mock_probability(processed_input)
            
            raw_output = {
                "logits": [base_probability - 0.5, base_probability + 0.5],
                "probabilities": [1 - base_probability, base_probability],
                "attention_weights": np.random.rand(10).tolist(),
                "hidden_states": np.random.rand(5).tolist(),
                "model_confidence": min(0.95, base_probability + 0.1)
            }
            
            logger.debug("Model inference completed")
            return raw_output
            
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            raise RuntimeError(f"Inference execution failed: {e}")
    
    def _calculate_mock_probability(self, processed_input: Dict[str, Any]) -> float:
        """Calculate a realistic mock probability based on input features."""
        # Use input features to generate a somewhat realistic probability
        wind_speed = processed_input.get("solar_wind_speed", 0.5)
        density = processed_input.get("proton_density", 0.5)
        temp = processed_input.get("temperature", 0.5)
        
        # Simple heuristic: higher values generally indicate higher flare probability
        base_prob = (wind_speed * 0.4 + density * 0.3 + temp * 0.3)
        
        # Add some randomness
        noise = np.random.normal(0, 0.1)
        probability = np.clip(base_prob + noise, 0.0, 1.0)
        
        return float(probability)
    
    async def _postprocess_output(self, raw_output: Dict[str, Any]) -> float:
        """
        Postprocess model output to extract flare probability.
        
        Args:
            raw_output: Raw model output
            
        Returns:
            Solar flare probability (0.0 to 1.0)
        """
        try:
            # Extract probability from model output
            if "probabilities" in raw_output and len(raw_output["probabilities"]) >= 2:
                # Assuming binary classification: [no_flare_prob, flare_prob]
                flare_probability = float(raw_output["probabilities"][1])
            else:
                # Fallback to logits if probabilities not available
                logits = raw_output.get("logits", [0.0, 0.5])
                flare_probability = 1.0 / (1.0 + np.exp(-logits[1]))  # Sigmoid
            
            # Ensure probability is in valid range
            flare_probability = np.clip(flare_probability, 0.0, 1.0)
            
            logger.debug(f"Extracted flare probability: {flare_probability}")
            return flare_probability
            
        except Exception as e:
            logger.error(f"Output postprocessing failed: {e}")
            raise RuntimeError(f"Failed to postprocess output: {e}")
    
    async def classify_severity(self, probability: float) -> SeverityLevel:
        """
        Classify solar flare severity based on probability.
        
        Args:
            probability: Flare probability (0.0 to 1.0)
            
        Returns:
            Severity level classification
        """
        try:
            if probability >= self.config.severity_thresholds["high"]:
                return SeverityLevel.HIGH
            elif probability >= self.config.severity_thresholds["medium"]:
                return SeverityLevel.MEDIUM
            else:
                return SeverityLevel.LOW
                
        except Exception as e:
            logger.error(f"Severity classification failed: {e}")
            return SeverityLevel.LOW  # Default to low severity on error
    
    async def _calculate_confidence(self, raw_output: Dict[str, Any]) -> float:
        """
        Calculate model confidence score.
        
        Args:
            raw_output: Raw model output
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            # Use model's internal confidence if available
            if "model_confidence" in raw_output:
                return float(np.clip(raw_output["model_confidence"], 0.0, 1.0))
            
            # Calculate confidence from probabilities
            if "probabilities" in raw_output:
                probs = raw_output["probabilities"]
                # Confidence is the maximum probability (how certain the model is)
                confidence = float(max(probs))
                return np.clip(confidence, 0.0, 1.0)
            
            # Default confidence
            return 0.5
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5  # Default confidence on error
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the model inference engine.
        
        Returns:
            Health status information
        """
        try:
            status = {
                "model_loaded": self._model_loaded,
                "model_name": self.config.model_name,
                "device": self.config.device,
                "last_check": datetime.utcnow().isoformat()
            }
            
            if self._model_loaded:
                # Test with dummy data
                dummy_data = SolarData(
                    timestamp=datetime.utcnow(),
                    magnetic_field_data=[1.0, 2.0, 3.0],
                    solar_wind_speed=400.0,
                    proton_density=5.0,
                    temperature=1_000_000.0
                )
                
                start_time = datetime.utcnow()
                await self.run_prediction(dummy_data)
                end_time = datetime.utcnow()
                
                status["test_prediction_success"] = True
                status["test_prediction_time_ms"] = (end_time - start_time).total_seconds() * 1000
            else:
                status["test_prediction_success"] = False
                status["test_prediction_time_ms"] = None
            
            return status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "model_loaded": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def check_model_health(self) -> bool:
        """
        Quick health check to determine if model is ready.
        
        Returns:
            True if model is healthy and ready for predictions
        """
        try:
            if not self._model_loaded:
                return False
            
            # Quick validation without full prediction
            return self.model is not None and self.tokenizer is not None
            
        except Exception as e:
            logger.error(f"Model health check failed: {e}")
            return False


class ModelInferenceService:
    """Service wrapper for model inference engine."""
    
    def __init__(self):
        self.engine = None
    
    async def get_engine(self) -> ModelInferenceEngine:
        """Get or create model engine instance."""
        if self.engine is None:
            self.engine = ModelInferenceEngine()
            await self.engine.initialize()
        return self.engine
    
    async def check_model_health(self) -> bool:
        """Check if model is healthy and ready."""
        try:
            engine = await self.get_engine()
            return await engine.check_model_health()
        except Exception:
            return False


# Global model instance
_model_engine: Optional[ModelInferenceEngine] = None


async def get_model_engine() -> ModelInferenceEngine:
    """
    Get or create the global model inference engine instance.
    
    Returns:
        Initialized model inference engine
    """
    global _model_engine
    
    if _model_engine is None:
        _model_engine = ModelInferenceEngine()
        await _model_engine.initialize()
    
    return _model_engine


async def shutdown_model_engine() -> None:
    """Shutdown the global model inference engine."""
    global _model_engine
    
    if _model_engine is not None:
        logger.info("Shutting down model inference engine")
        _model_engine = None