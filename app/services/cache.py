"""
Redis Cache Service
Handles caching for NASA API responses and rate limiting
"""

import json
import structlog
from typing import Optional, Any, Union
from datetime import datetime

logger = structlog.get_logger()

# Try to import redis, provide fallback if not available
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis_not_available", message="Using in-memory cache fallback")


class InMemoryCache:
    """Fallback in-memory cache when Redis is not available"""
    
    def __init__(self):
        self._cache: dict = {}
        self._expiry: dict = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if key in self._expiry:
                if datetime.utcnow().timestamp() > self._expiry[key]:
                    del self._cache[key]
                    del self._expiry[key]
                    return None
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        self._expiry[key] = datetime.utcnow().timestamp() + ttl
    
    async def delete(self, key: str):
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
    
    async def incr(self, key: str) -> int:
        current = self._cache.get(key, 0)
        self._cache[key] = current + 1
        return self._cache[key]
    
    async def expire(self, key: str, seconds: int):
        self._expiry[key] = datetime.utcnow().timestamp() + seconds
    
    async def close(self):
        pass


class CacheService:
    """
    Redis cache service with in-memory fallback
    
    Used for:
    - NASA API response caching (5 min TTL)
    - Rate limit counters (24h TTL)
    - Session data (1h TTL)
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._client: Optional[Union[redis.Redis, InMemoryCache]] = None
        self._connected = False
    
    async def connect(self):
        """Initialize connection to Redis or fallback"""
        if self._connected:
            return
        
        if REDIS_AVAILABLE and self.redis_url:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self._client.ping()
                self._connected = True
                logger.info("redis_connected", url=self.redis_url[:20] + "...")
            except Exception as e:
                logger.warning("redis_connection_failed", error=str(e))
                self._client = InMemoryCache()
                self._connected = True
        else:
            self._client = InMemoryCache()
            self._connected = True
            logger.info("using_inmemory_cache")
    
    async def _ensure_connected(self):
        if not self._connected:
            await self.connect()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value, returns None if not found or expired"""
        await self._ensure_connected()
        
        try:
            if isinstance(self._client, InMemoryCache):
                return await self._client.get(key)
            
            value = await self._client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set cache with TTL in seconds"""
        await self._ensure_connected()
        
        try:
            if isinstance(self._client, InMemoryCache):
                await self._client.set(key, value, ttl)
            else:
                serialized = json.dumps(value) if not isinstance(value, str) else value
                await self._client.setex(key, ttl, serialized)
            
            logger.debug("cache_set", key=key, ttl=ttl)
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
    
    async def delete(self, key: str):
        """Delete a cache key"""
        await self._ensure_connected()
        
        try:
            await self._client.delete(key)
            logger.debug("cache_deleted", key=key)
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
    
    async def increment_rate_limit(self, user_id: str, window: str = "day") -> int:
        """
        Increment and return request count for rate limiting
        
        Args:
            user_id: User identifier
            window: Time window - 'day', 'hour', or 'minute'
            
        Returns:
            Current count for this window
        """
        await self._ensure_connected()
        
        now = datetime.utcnow()
        if window == "day":
            key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d')}"
            ttl = 86400
        elif window == "hour":
            key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d-%H')}"
            ttl = 3600
        else:
            key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d-%H-%M')}"
            ttl = 60
        
        try:
            if isinstance(self._client, InMemoryCache):
                count = await self._client.incr(key)
                await self._client.expire(key, ttl)
            else:
                count = await self._client.incr(key)
                # Set expiry on first increment
                if count == 1:
                    await self._client.expire(key, ttl)
            
            return count
        except Exception as e:
            logger.error("rate_limit_increment_error", user_id=user_id, error=str(e))
            return 0
    
    async def get_rate_limit_count(self, user_id: str, window: str = "day") -> int:
        """Get current rate limit count for user"""
        await self._ensure_connected()
        
        now = datetime.utcnow()
        if window == "day":
            key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d')}"
        elif window == "hour":
            key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d-%H')}"
        else:
            key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d-%H-%M')}"
        
        try:
            if isinstance(self._client, InMemoryCache):
                value = await self._client.get(key)
            else:
                value = await self._client.get(key)
            
            return int(value) if value else 0
        except Exception as e:
            logger.error("rate_limit_get_error", user_id=user_id, error=str(e))
            return 0
    
    async def set_with_lock(self, key: str, value: Any, ttl: int = 300, lock_timeout: int = 10) -> bool:
        """
        Set value only if key doesn't exist (distributed lock pattern)
        
        Returns:
            True if value was set (lock acquired), False otherwise
        """
        await self._ensure_connected()
        
        try:
            if isinstance(self._client, InMemoryCache):
                existing = await self._client.get(key)
                if existing is None:
                    await self._client.set(key, value, ttl)
                    return True
                return False
            else:
                serialized = json.dumps(value) if not isinstance(value, str) else value
                result = await self._client.set(key, serialized, nx=True, ex=ttl)
                return result is not None
        except Exception as e:
            logger.error("cache_lock_error", key=key, error=str(e))
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._client and self._connected:
            try:
                await self._client.close()
                logger.info("cache_connection_closed")
            except Exception as e:
                logger.error("cache_close_error", error=str(e))
        self._connected = False


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service(redis_url: Optional[str] = None) -> CacheService:
    """Get or create cache service singleton"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(redis_url=redis_url)
    return _cache_service
