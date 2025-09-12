"""Repository for API usage tracking and analytics."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from app.repositories.base import BaseRepository
from app.models.core import APIUsageRecord

logger = logging.getLogger(__name__)


class APIUsageRepository(BaseRepository[APIUsageRecord]):
    """Repository for managing API usage tracking."""
    
    def __init__(self):
        super().__init__("api_usage")
    
    def _row_to_model(self, row: Dict[str, Any]) -> APIUsageRecord:
        """Convert database row to APIUsageRecord model."""
        return APIUsageRecord(
            id=row.get('id'),
            user_id=row.get('user_id'),
            subscription_id=row.get('subscription_id'),
            endpoint=row['endpoint'],
            method=row.get('method', 'GET'),
            status_code=row['status_code'],
            response_time_ms=row.get('response_time_ms'),
            request_size_bytes=row.get('request_size_bytes'),
            response_size_bytes=row.get('response_size_bytes'),
            ip_address=row.get('ip_address'),
            user_agent=row.get('user_agent'),
            api_key_used=row.get('api_key_used', False),
            rate_limit_hit=row.get('rate_limit_hit', False),
            timestamp=row.get('timestamp')
        )
    
    def _model_to_dict(self, model: APIUsageRecord) -> Dict[str, Any]:
        """Convert APIUsageRecord model to dictionary."""
        return {
            'id': model.id,
            'user_id': model.user_id,
            'subscription_id': model.subscription_id,
            'endpoint': model.endpoint,
            'method': model.method,
            'status_code': model.status_code,
            'response_time_ms': model.response_time_ms,
            'request_size_bytes': model.request_size_bytes,
            'response_size_bytes': model.response_size_bytes,
            'ip_address': model.ip_address,
            'user_agent': model.user_agent,
            'api_key_used': model.api_key_used,
            'rate_limit_hit': model.rate_limit_hit,
            'timestamp': model.timestamp
        }
    
    async def log_api_call(
        self,
        user_id: Optional[str],
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: Optional[int] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        api_key_used: bool = False,
        rate_limit_hit: bool = False
    ) -> Optional[APIUsageRecord]:
        """
        Log an API call.
        
        Args:
            user_id: User ID making the call (None for anonymous)
            endpoint: API endpoint called
            method: HTTP method
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            request_size_bytes: Request size in bytes
            response_size_bytes: Response size in bytes
            ip_address: Client IP address
            user_agent: Client user agent
            api_key_used: Whether API key was used for authentication
            rate_limit_hit: Whether rate limit was hit
            
        Returns:
            Created APIUsageRecord if successful, None otherwise
        """
        usage_record = APIUsageRecord(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            ip_address=ip_address,
            user_agent=user_agent,
            api_key_used=api_key_used,
            rate_limit_hit=rate_limit_hit,
            timestamp=datetime.utcnow()
        )
        
        return await self.create(usage_record)
    
    async def get_usage_by_user(
        self, 
        user_id: str, 
        hours_back: int = 24,
        limit: Optional[int] = None
    ) -> List[APIUsageRecord]:
        """
        Get API usage for a specific user.
        
        Args:
            user_id: User ID to get usage for
            hours_back: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of APIUsageRecord instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT * FROM api_usage 
                WHERE user_id = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
            """
            params = [user_id, cutoff_time]
            
            if limit:
                query += f" LIMIT ${len(params) + 1}"
                params.append(limit)
            
            results = await db_manager.execute_query(query, *params, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get usage by user: {e}")
            return []
    
    async def get_usage_by_endpoint(
        self, 
        endpoint: str, 
        hours_back: int = 24
    ) -> List[APIUsageRecord]:
        """
        Get API usage for a specific endpoint.
        
        Args:
            endpoint: Endpoint to get usage for
            hours_back: Number of hours to look back
            
        Returns:
            List of APIUsageRecord instances
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT * FROM api_usage 
                WHERE endpoint = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
            """
            
            results = await db_manager.execute_query(query, endpoint, cutoff_time, fetch_all=True)
            
            return [self._row_to_model(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to get usage by endpoint: {e}")
            return []
    
    async def get_user_request_count(self, user_id: str, hours_back: int = 1) -> int:
        """
        Get request count for a user in the specified time period.
        
        Args:
            user_id: User ID to count requests for
            hours_back: Number of hours to look back
            
        Returns:
            Number of requests made by the user
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT COUNT(*) as count FROM api_usage 
                WHERE user_id = $1 AND timestamp >= $2
            """
            
            result = await db_manager.execute_query(query, user_id, cutoff_time, fetch_one=True)
            
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to get user request count: {e}")
            return 0
    
    async def get_endpoint_statistics(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get statistics for all endpoints.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            List of endpoint statistics
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT 
                    endpoint,
                    COUNT(*) as request_count,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(response_time_ms) as max_response_time,
                    COUNT(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 END) as success_count,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                    COUNT(CASE WHEN rate_limit_hit = true THEN 1 END) as rate_limit_hits
                FROM api_usage 
                WHERE timestamp >= $1
                GROUP BY endpoint
                ORDER BY request_count DESC
            """
            
            results = await db_manager.execute_query(query, cutoff_time, fetch_all=True)
            
            return [
                {
                    'endpoint': row['endpoint'],
                    'request_count': row['request_count'],
                    'avg_response_time': float(row['avg_response_time']) if row['avg_response_time'] else 0.0,
                    'max_response_time': row['max_response_time'] or 0,
                    'success_count': row['success_count'],
                    'error_count': row['error_count'],
                    'rate_limit_hits': row['rate_limit_hits'],
                    'success_rate': (row['success_count'] / row['request_count'] * 100) if row['request_count'] > 0 else 0.0
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get endpoint statistics: {e}")
            return []
    
    async def get_user_statistics(self, user_id: str, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get usage statistics for a specific user.
        
        Args:
            user_id: User ID to get statistics for
            hours_back: Number of hours to analyze
            
        Returns:
            Dictionary with user usage statistics
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 END) as success_count,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                    COUNT(CASE WHEN rate_limit_hit = true THEN 1 END) as rate_limit_hits,
                    COUNT(CASE WHEN api_key_used = true THEN 1 END) as api_key_requests,
                    COUNT(DISTINCT endpoint) as unique_endpoints
                FROM api_usage 
                WHERE user_id = $1 AND timestamp >= $2
            """
            
            result = await db_manager.execute_query(query, user_id, cutoff_time, fetch_one=True)
            
            if result:
                total_requests = result['total_requests']
                return {
                    'total_requests': total_requests,
                    'avg_response_time': float(result['avg_response_time']) if result['avg_response_time'] else 0.0,
                    'success_count': result['success_count'],
                    'error_count': result['error_count'],
                    'rate_limit_hits': result['rate_limit_hits'],
                    'api_key_requests': result['api_key_requests'],
                    'unique_endpoints': result['unique_endpoints'],
                    'success_rate': (result['success_count'] / total_requests * 100) if total_requests > 0 else 0.0,
                    'hours_analyzed': hours_back
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return {}
    
    async def get_hourly_usage_stats(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get hourly usage statistics.
        
        Args:
            hours_back: Number of hours to analyze
            
        Returns:
            List of hourly usage statistics
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    COUNT(*) as request_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                    COUNT(CASE WHEN rate_limit_hit = true THEN 1 END) as rate_limit_hits
                FROM api_usage 
                WHERE timestamp >= $1
                GROUP BY DATE_TRUNC('hour', timestamp)
                ORDER BY hour DESC
            """
            
            results = await db_manager.execute_query(query, cutoff_time, fetch_all=True)
            
            return [
                {
                    'hour': row['hour'],
                    'request_count': row['request_count'],
                    'unique_users': row['unique_users'],
                    'avg_response_time': float(row['avg_response_time']) if row['avg_response_time'] else 0.0,
                    'error_count': row['error_count'],
                    'rate_limit_hits': row['rate_limit_hits']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get hourly usage stats: {e}")
            return []
    
    async def cleanup_old_usage_records(self, days_to_keep: int = 90) -> int:
        """
        Delete old usage records to manage database size.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # First count how many will be deleted
            count_query = "SELECT COUNT(*) as count FROM api_usage WHERE timestamp < $1"
            count_result = await db_manager.execute_query(count_query, cutoff_date, fetch_one=True)
            delete_count = count_result['count'] if count_result else 0
            
            if delete_count > 0:
                # Delete old records
                delete_query = "DELETE FROM api_usage WHERE timestamp < $1"
                await db_manager.execute_query(delete_query, cutoff_date)
                
                logger.info(f"Deleted {delete_count} old usage records (older than {days_to_keep} days)")
            
            return delete_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old usage records: {e}")
            return 0
    
    async def get_top_users_by_usage(self, hours_back: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users by API usage.
        
        Args:
            hours_back: Number of hours to analyze
            limit: Maximum number of users to return
            
        Returns:
            List of top users with usage statistics
        """
        try:
            db_manager = await self._get_db_manager()
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            query = """
                SELECT 
                    user_id,
                    COUNT(*) as request_count,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                    COUNT(CASE WHEN rate_limit_hit = true THEN 1 END) as rate_limit_hits
                FROM api_usage 
                WHERE user_id IS NOT NULL AND timestamp >= $1
                GROUP BY user_id
                ORDER BY request_count DESC
                LIMIT $2
            """
            
            results = await db_manager.execute_query(query, cutoff_time, limit, fetch_all=True)
            
            return [
                {
                    'user_id': row['user_id'],
                    'request_count': row['request_count'],
                    'avg_response_time': float(row['avg_response_time']) if row['avg_response_time'] else 0.0,
                    'error_count': row['error_count'],
                    'rate_limit_hits': row['rate_limit_hits']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to get top users by usage: {e}")
            return []


# Global repository instance
api_usage_repository = APIUsageRepository()


def get_api_usage_repository() -> APIUsageRepository:
    """Get the global API usage repository instance."""
    return api_usage_repository