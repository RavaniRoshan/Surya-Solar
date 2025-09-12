"""Repository for solar flare predictions data access."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from app.repositories.base import BaseRepository
from app.models.core import PredictionResult, SeverityLevel

logger = logging.getLogger(__name__)


class PredictionsRepository(BaseRepository[PredictionResult]):
    """Repository for managing solar flare predictions."""
    
    def __init__(self):
        super().__init__("predictions")
    
    def _row_to_model(self, row: Dict[str, Any]) -> PredictionResult:
        """Convert database row to PredictionResult model."""
        return PredictionResult(
            id=row.get('id'),
            timestamp=row['timestamp'],
            flare_probability=float(row['flare_probability']),
            severity_level=SeverityLevel(row['severity_level']),
            model_version=row.get('model_version', 'surya-1.0'),
            confidence_score=float(row['confidence_score']) if row.get('confidence_score') else None,
            raw_output=row.get('raw_output', {}),
            solar_data=row.get('solar_data', {}),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )
    
    def _model_to_dict(self, model: PredictionResult) -> Dict[str, Any]:
        """Convert PredictionResult model to dictionary."""
        return {
            'id': model.id,
            'timestamp': model.timestamp,
            'flare_probability': model.flare_probability,
            'severity_level': model.severity_level.value,
            'model_version': model.model_version,
            'confidence_score': model.confidence_score,
            'raw_output': model.raw_output,
            'solar_data': model.solar_data,
            'created_at': model.created_at,
            'updated_at': model.updated_at
        }
    
    async def get_current_prediction(self) -> Optional[PredictionResult]:
        """
        Get the most recent prediction.
        
        Returns:
            Most recent PredictionResult or None
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = """
                SELECT * FROM predictions 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            
            result = await db_manager.execute_query(query, fetch_one=True)
            
            if result:
                return self._row_to_model(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get current prediction: {e}")
            return None
    
    async def get_predictions_by_time_range(
        self, 
        start_time: datetime, 
        end_time: datetime,
        limit: Optional[int] = None
    ) -> List[PredictionResult]:
        """
        Get predictions within a specific time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of predictions to return
            
        Returns:
            List of PredictionResult instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = """
                SELECT * FROM predictions 
                WHERE timestamp >= $1 AND timestamp <= $2
                ORDER BY timestamp DESC
            """
            params = [start_time, end_time]
            
            if limit:
                query += f" LIMIT ${len(params) + 1}"
                params.append(limit)
            
            results = await db_manager.execute_query(query, *params, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get predictions by time range: {e}")
            return []
    
    async def get_predictions_last_24_hours(self) -> List[PredictionResult]:
        """
        Get all predictions from the last 24 hours.
        
        Returns:
            List of PredictionResult instances from last 24 hours
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        return await self.get_predictions_by_time_range(start_time, end_time)
    
    async def get_predictions_by_severity(
        self, 
        severity: SeverityLevel,
        hours_back: Optional[int] = None
    ) -> List[PredictionResult]:
        """
        Get predictions by severity level.
        
        Args:
            severity: Severity level to filter by
            hours_back: Number of hours to look back (None for all time)
            
        Returns:
            List of PredictionResult instances with specified severity
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = "SELECT * FROM predictions WHERE severity_level = $1"
            params = [severity.value]
            
            if hours_back:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
                query += " AND timestamp >= $2"
                params.append(cutoff_time)
            
            query += " ORDER BY timestamp DESC"
            
            results = await db_manager.execute_query(query, *params, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get predictions by severity: {e}")
            return []
    
    async def get_high_severity_predictions(self, hours_back: int = 24) -> List[PredictionResult]:
        """
        Get high severity predictions from recent hours.
        
        Args:
            hours_back: Number of hours to look back
            
        Returns:
            List of high severity PredictionResult instances
        """
        return await self.get_predictions_by_severity(SeverityLevel.HIGH, hours_back)
    
    async def get_predictions_above_threshold(
        self, 
        probability_threshold: float,
        hours_back: Optional[int] = None
    ) -> List[PredictionResult]:
        """
        Get predictions above a probability threshold.
        
        Args:
            probability_threshold: Minimum probability threshold (0.0 to 1.0)
            hours_back: Number of hours to look back (None for all time)
            
        Returns:
            List of PredictionResult instances above threshold
        """
        try:
            db_manager = await self._get_db_manager()
            
            query = "SELECT * FROM predictions WHERE flare_probability >= $1"
            params = [probability_threshold]
            
            if hours_back:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
                query += " AND timestamp >= $2"
                params.append(cutoff_time)
            
            query += " ORDER BY timestamp DESC"
            
            results = await db_manager.execute_query(query, *params, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get predictions above threshold: {e}")
            return []
    
    async def get_prediction_statistics(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get prediction statistics for the specified time period.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            Dictionary with prediction statistics
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    AVG(flare_probability) as avg_probability,
                    MAX(flare_probability) as max_probability,
                    MIN(flare_probability) as min_probability,
                    COUNT(CASE WHEN severity_level = 'high' THEN 1 END) as high_count,
                    COUNT(CASE WHEN severity_level = 'medium' THEN 1 END) as medium_count,
                    COUNT(CASE WHEN severity_level = 'low' THEN 1 END) as low_count
                FROM predictions 
                WHERE timestamp >= $1
            """
            
            result = await db_manager.execute_query(query, cutoff_time, fetch_one=True)
            
            if result:
                return {
                    'total_predictions': result['total_predictions'],
                    'avg_probability': float(result['avg_probability']) if result['avg_probability'] else 0.0,
                    'max_probability': float(result['max_probability']) if result['max_probability'] else 0.0,
                    'min_probability': float(result['min_probability']) if result['min_probability'] else 0.0,
                    'high_severity_count': result['high_count'],
                    'medium_severity_count': result['medium_count'],
                    'low_severity_count': result['low_count'],
                    'hours_analyzed': hours_back
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get prediction statistics: {e}")
            return {}
    
    async def delete_old_predictions(self, days_to_keep: int = 30) -> int:
        """
        Delete predictions older than specified days.
        
        Args:
            days_to_keep: Number of days of predictions to keep
            
        Returns:
            Number of predictions deleted
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # First count how many will be deleted
            count_query = "SELECT COUNT(*) as count FROM predictions WHERE timestamp < $1"
            count_result = await db_manager.execute_query(count_query, cutoff_date, fetch_one=True)
            delete_count = count_result['count'] if count_result else 0
            
            if delete_count > 0:
                # Delete old predictions
                delete_query = "DELETE FROM predictions WHERE timestamp < $1"
                await db_manager.execute_query(delete_query, cutoff_date)
                
                logger.info(f"Deleted {delete_count} old predictions (older than {days_to_keep} days)")
            
            return delete_count
            
        except Exception as e:
            logger.error(f"Failed to delete old predictions: {e}")
            return 0
    
    async def get_hourly_prediction_counts(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get prediction counts grouped by hour.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            List of hourly prediction counts
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    COUNT(*) as prediction_count,
                    AVG(flare_probability) as avg_probability,
                    MAX(flare_probability) as max_probability
                FROM predictions 
                WHERE timestamp >= $1
                GROUP BY DATE_TRUNC('hour', timestamp)
                ORDER BY hour DESC
            """
            
            results = await db_manager.execute_query(query, cutoff_time, fetch_all=True)
            
            return [
                {
                    'hour': row['hour'],
                    'prediction_count': row['prediction_count'],
                    'avg_probability': float(row['avg_probability']) if row['avg_probability'] else 0.0,
                    'max_probability': float(row['max_probability']) if row['max_probability'] else 0.0
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get hourly prediction counts: {e}")
            return []


# Global repository instance
predictions_repository = PredictionsRepository()


def get_predictions_repository() -> PredictionsRepository:
    """Get the global predictions repository instance."""
    return predictions_repository