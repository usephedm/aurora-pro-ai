"""
Aurora Pro AI - Redis Cache Management
"""
import json
from typing import Any, Optional
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger("cache")
settings = get_settings()


class RedisCache:
    """Redis cache manager with connection pooling"""
    
    def __init__(self):
        self.pool = redis.ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
            max_connections=50
        )
        self.client = redis.Redis(connection_pool=self.pool)
        logger.info("Redis cache initialized")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get failed: {e}", extra={"key": key})
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            logger.debug("Cache set successful", extra={"key": key, "ttl": ttl})
            return True
        except Exception as e:
            logger.error(f"Cache set failed: {e}", extra={"key": key})
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.client.delete(key)
            logger.debug("Cache delete successful", extra={"key": key})
            return True
        except Exception as e:
            logger.error(f"Cache delete failed: {e}", extra={"key": key})
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists check failed: {e}", extra={"key": key})
            return False
    
    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance"""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
