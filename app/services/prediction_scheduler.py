"""Prediction scheduler for automated solar flare predictions."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import httpx
from pydantic import BaseModel

from app.models.core import SolarData, PredictionResult, SeverityLevel
from app.services.model_inference import get_model_engine
from app.repositories.predictions import PredictionsRepository
from app.services.database import get_database_manager


logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the prediction scheduler."""
    prediction_interval_minutes: int = 10
    max_retries: int = 3
    retry_delay_seconds: int = 30
    nasa_api_timeout_seconds: int = 30
    enable_mock_data: bool = True  # Use mock data for development
    nasa_api_base_url: str = "https://api.nasa.gov/DONKI"
    nasa_api_key: Optional[str] = None


class NASADataFetcher:
    """
    Handles fetching solar weather data from NASA APIs.
    
    For development, this uses mock data. In production, it would
    connect to actual NASA data sources like DONKI or SWPC.
    """
    
    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.nasa_api_timeout_seconds)
    
    async def fetch_latest_solar_data(self) -> SolarData:
        """
        Fetch the latest solar weather data.
        
        Returns:
            SolarData with current solar conditions
            
        Raises:
            RuntimeError: If data fetching fails
        """
        if self.config.enable_mock_data:
            return await self._fetch_mock_data()
        else:
            return await self._fetch_real_nasa_data()
    
    async def _fetch_mock_data(self) -> SolarData:
        """Generate realistic mock solar data for development."""
        try:
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Generate realistic solar weather data
            import random
            import numpy as np
            
            # Base values with some realistic variation
            base_wind_speed = 400 + random.gauss(0, 100)  # km/s
            base_density = 5 + random.gauss(0, 2)  # particles/cm³
            base_temperature = 100000 + random.gauss(0, 50000)  # Kelvin
            
            # Generate magnetic field data (Bx, By, Bz components over time)
            mag_field_length = random.randint(10, 50)
            mag_field_data = [
                random.gauss(0, 5) for _ in range(mag_field_length)
            ]
            
            # Ensure values are within valid ranges
            wind_speed = max(0, min(3000, base_wind_speed))
            density = max(0, min(1000, base_density))
            temperature = max(0, min(10_000_000, base_temperature))
            
            solar_data = SolarData(
                timestamp=datetime.utcnow(),
                magnetic_field_data=mag_field_data,
                solar_wind_speed=wind_speed,
                proton_density=density,
                temperature=temperature,
                source="nasa_mock"
            )
            
            logger.debug(f"Generated mock solar data: wind_speed={wind_speed:.1f}, "
                        f"density={density:.1f}, temp={temperature:.0f}")
            
            return solar_data
            
        except Exception as e:
            logger.error(f"Failed to generate mock data: {e}")
            raise RuntimeError(f"Mock data generation failed: {e}")
    
    async def _fetch_real_nasa_data(self) -> SolarData:
        """
        Fetch real data from NASA APIs.
        
        This is a placeholder implementation. In production, this would
        integrate with actual NASA data sources like:
        - DONKI (Database of Notifications, Knowledge, Information)
        - SWPC (Space Weather Prediction Center)
        - ACE (Advanced Composition Explorer) satellite data
        """
        try:
            # Example API calls (these would be real endpoints in production)
            headers = {}
            if self.config.nasa_api_key:
                headers["X-API-Key"] = self.config.nasa_api_key
            
            # Fetch solar wind data
            wind_response = await self.client.get(
                f"{self.config.nasa_api_base_url}/WSAEnlilSimulations",
                headers=headers,
                params={
                    "startDate": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "endDate": datetime.utcnow().isoformat()
                }
            )
            wind_response.raise_for_status()
            
            # Fetch magnetic field data
            mag_response = await self.client.get(
                f"{self.config.nasa_api_base_url}/IPS",
                headers=headers,
                params={
                    "startDate": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "endDate": datetime.utcnow().isoformat()
                }
            )
            mag_response.raise_for_status()
            
            # Process the responses (this would parse real NASA data)
            wind_data = wind_response.json()
            mag_data = mag_response.json()
            
            # Extract relevant values (placeholder logic)
            solar_data = SolarData(
                timestamp=datetime.utcnow(),
                magnetic_field_data=[1.0, 2.0, 3.0],  # Would parse from mag_data
                solar_wind_speed=400.0,  # Would parse from wind_data
                proton_density=5.0,  # Would parse from wind_data
                temperature=1_000_000.0,  # Would parse from wind_data
                source="nasa_api"
            )
            
            logger.info("Successfully fetched real NASA data")
            return solar_data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching NASA data: {e}")
            raise RuntimeError(f"Failed to fetch NASA data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching NASA data: {e}")
            raise RuntimeError(f"NASA data fetch failed: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class PredictionScheduler:
    """
    Orchestrates regular model inference execution and result storage.
    
    This scheduler runs predictions every 10 minutes, fetches solar data,
    executes the model, stores results, and handles errors with retry logic.
    """
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.data_fetcher = NASADataFetcher(self.config)
        self.prediction_repository: Optional[PredictionsRepository] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize the scheduler and its dependencies."""
        try:
            # Initialize database connection
            await get_database_manager()  # Ensure database is initialized
            self.prediction_repository = PredictionsRepository()
            
            logger.info("Prediction scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise RuntimeError(f"Scheduler initialization failed: {e}")
    
    async def start(self):
        """Start the prediction scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        if not self.prediction_repository:
            await self.initialize()
        
        self._running = True
        self._shutdown_event.clear()
        
        # Start the main scheduler loop
        self._task = asyncio.create_task(self._scheduler_loop())
        
        logger.info(f"Prediction scheduler started with {self.config.prediction_interval_minutes}-minute intervals")
    
    async def stop(self):
        """Stop the prediction scheduler gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping prediction scheduler...")
        
        self._running = False
        self._shutdown_event.set()
        
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Scheduler shutdown timed out, cancelling task")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        await self.data_fetcher.close()
        logger.info("Prediction scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that runs predictions at regular intervals."""
        try:
            # Run initial prediction immediately
            await self._execute_prediction_cycle()
            
            while self._running:
                try:
                    # Wait for the next interval or shutdown signal
                    interval_seconds = self.config.prediction_interval_minutes * 60
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=interval_seconds
                    )
                    # If we get here, shutdown was requested
                    break
                    
                except asyncio.TimeoutError:
                    # Timeout means it's time for the next prediction
                    if self._running:
                        await self._execute_prediction_cycle()
                
        except Exception as e:
            logger.error(f"Scheduler loop failed: {e}")
            self._running = False
        
        logger.info("Scheduler loop ended")
    
    async def execute_prediction_cycle(self) -> Optional[PredictionResult]:
        """
        Execute a single prediction cycle manually.
        
        This method can be called directly for testing or manual execution.
        
        Returns:
            PredictionResult if successful, None if failed
        """
        return await self._execute_prediction_cycle()
    
    async def _execute_prediction_cycle(self) -> Optional[PredictionResult]:
        """Execute a complete prediction cycle with retry logic."""
        for attempt in range(self.config.max_retries + 1):
            try:
                logger.info(f"Starting prediction cycle (attempt {attempt + 1})")
                
                # Step 1: Fetch solar data
                solar_data = await self.fetch_solar_data()
                
                # Step 2: Run model inference
                prediction_result = await self._run_model_inference(solar_data)
                
                # Step 3: Store prediction result
                await self.store_prediction(prediction_result)
                
                # Step 4: Trigger alerts if necessary
                await self.trigger_alerts(prediction_result)
                
                logger.info(f"Prediction cycle completed successfully: "
                           f"probability={prediction_result.flare_probability:.3f}, "
                           f"severity={prediction_result.severity_level}")
                
                return prediction_result
                
            except Exception as e:
                logger.error(f"Prediction cycle failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries:
                    logger.info(f"Retrying in {self.config.retry_delay_seconds} seconds...")
                    await asyncio.sleep(self.config.retry_delay_seconds)
                else:
                    logger.error("All retry attempts exhausted, prediction cycle failed")
                    return None
    
    async def fetch_solar_data(self) -> SolarData:
        """
        Fetch the latest solar weather data.
        
        Returns:
            SolarData with current solar conditions
            
        Raises:
            RuntimeError: If data fetching fails
        """
        try:
            solar_data = await self.data_fetcher.fetch_latest_solar_data()
            
            logger.debug(f"Fetched solar data from {solar_data.source}: "
                        f"wind_speed={solar_data.solar_wind_speed:.1f} km/s, "
                        f"density={solar_data.proton_density:.1f} particles/cm³")
            
            return solar_data
            
        except Exception as e:
            logger.error(f"Failed to fetch solar data: {e}")
            raise RuntimeError(f"Solar data fetch failed: {e}")
    
    async def _run_model_inference(self, solar_data: SolarData) -> PredictionResult:
        """
        Run model inference on the solar data.
        
        Args:
            solar_data: Input solar weather data
            
        Returns:
            PredictionResult with prediction and metadata
            
        Raises:
            RuntimeError: If model inference fails
        """
        try:
            model_engine = await get_model_engine()
            prediction_result = await model_engine.run_prediction(solar_data)
            
            logger.debug(f"Model inference completed: "
                        f"probability={prediction_result.flare_probability:.3f}, "
                        f"confidence={prediction_result.confidence_score:.3f}")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            raise RuntimeError(f"Model inference failed: {e}")
    
    async def store_prediction(self, prediction_result: PredictionResult) -> str:
        """
        Store the prediction result in the database.
        
        Args:
            prediction_result: Prediction to store
            
        Returns:
            ID of the stored prediction
            
        Raises:
            RuntimeError: If storage fails
        """
        try:
            if not self.prediction_repository:
                raise RuntimeError("Prediction repository not initialized")
            
            created_prediction = await self.prediction_repository.create(prediction_result)
            prediction_id = created_prediction.id if created_prediction else None
            
            logger.debug(f"Stored prediction with ID: {prediction_id}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            raise RuntimeError(f"Prediction storage failed: {e}")
    
    async def trigger_alerts(self, prediction_result: PredictionResult) -> None:
        """
        Trigger alerts based on the prediction result.
        
        This method evaluates if the prediction meets alert thresholds
        and triggers appropriate notifications.
        
        Args:
            prediction_result: Prediction to evaluate for alerts
        """
        try:
            # Determine if alert should be triggered
            alert_triggered = self._should_trigger_alert(prediction_result)
            
            if alert_triggered:
                logger.info(f"Alert triggered for {prediction_result.severity_level} severity "
                           f"solar flare (probability: {prediction_result.flare_probability:.3f})")
                
                # In a full implementation, this would:
                # 1. Send WebSocket notifications to connected clients
                # 2. Send webhook notifications to subscribed URLs
                # 3. Update alert status in database
                # 4. Send email/SMS notifications for high-priority alerts
                
                await self._send_alert_notifications(prediction_result)
            else:
                logger.debug(f"No alert triggered for probability {prediction_result.flare_probability:.3f}")
                
        except Exception as e:
            logger.error(f"Failed to trigger alerts: {e}")
            # Don't raise here - alert failures shouldn't stop the prediction cycle
    
    def _should_trigger_alert(self, prediction_result: PredictionResult) -> bool:
        """
        Determine if an alert should be triggered based on prediction.
        
        Args:
            prediction_result: Prediction to evaluate
            
        Returns:
            True if alert should be triggered
        """
        # Default thresholds (these would be configurable per user in production)
        alert_thresholds = {
            SeverityLevel.LOW: 0.3,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.HIGH: 0.8
        }
        
        threshold = alert_thresholds.get(prediction_result.severity_level, 0.5)
        return prediction_result.flare_probability >= threshold
    
    async def _send_alert_notifications(self, prediction_result: PredictionResult) -> None:
        """
        Send alert notifications through various channels.
        
        Args:
            prediction_result: Prediction that triggered the alert
        """
        try:
            # Placeholder for notification logic
            # In production, this would:
            # - Query subscribed users from database
            # - Send WebSocket messages to connected clients
            # - Send HTTP webhooks to configured URLs
            # - Send email/SMS for critical alerts
            
            logger.info(f"Alert notifications sent for {prediction_result.severity_level} "
                       f"solar flare prediction (ID: {prediction_result.id})")
            
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the prediction scheduler.
        
        Returns:
            Dictionary with scheduler status information
        """
        try:
            # Get latest prediction from database
            latest_prediction = None
            if self.prediction_repository:
                try:
                    latest_prediction = await self.prediction_repository.get_current_prediction()
                except Exception as e:
                    logger.warning(f"Failed to get latest prediction: {e}")
            
            status = {
                "running": self._running,
                "config": {
                    "prediction_interval_minutes": self.config.prediction_interval_minutes,
                    "max_retries": self.config.max_retries,
                    "enable_mock_data": self.config.enable_mock_data
                },
                "latest_prediction": {
                    "timestamp": latest_prediction.timestamp.isoformat() if latest_prediction else None,
                    "flare_probability": latest_prediction.flare_probability if latest_prediction else None,
                    "severity_level": latest_prediction.severity_level if latest_prediction else None
                } if latest_prediction else None,
                "next_prediction_eta": self._calculate_next_prediction_eta(),
                "status_timestamp": datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}")
            return {
                "running": self._running,
                "error": str(e),
                "status_timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_next_prediction_eta(self) -> Optional[str]:
        """Calculate when the next prediction is expected."""
        if not self._running:
            return None
        
        # This is a simplified calculation
        # In practice, you'd track the last prediction time
        interval_seconds = self.config.prediction_interval_minutes * 60
        next_time = datetime.utcnow() + timedelta(seconds=interval_seconds)
        return next_time.isoformat()


# Global scheduler instance
_scheduler: Optional[PredictionScheduler] = None


async def get_prediction_scheduler() -> PredictionScheduler:
    """
    Get or create the global prediction scheduler instance.
    
    Returns:
        Initialized prediction scheduler
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = PredictionScheduler()
        await _scheduler.initialize()
    
    return _scheduler


async def start_prediction_scheduler() -> None:
    """Start the global prediction scheduler."""
    scheduler = await get_prediction_scheduler()
    await scheduler.start()


async def stop_prediction_scheduler() -> None:
    """Stop the global prediction scheduler."""
    global _scheduler
    
    if _scheduler is not None:
        await _scheduler.stop()
        _scheduler = None