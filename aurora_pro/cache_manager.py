"""Advanced Caching System for Aurora Pro - Multi-tier cache with LRU eviction.

This module provides a high-performance caching system with memory cache (8GB max),
disk cache (diskcache), and optional Redis support. Includes LRU eviction and cache
invalidation strategies.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import pickle
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import aiofiles

logger = logging.getLogger(__name__)


class MemoryCache:
    """In-memory LRU cache with size limits."""

    def __init__(self, max_size_mb: int = 1024):
        self._cache: OrderedDict = OrderedDict()
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._current_size_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                value, size, timestamp = self._cache.pop(key)
                self._cache[key] = (value, size, timestamp)
                self._hits += 1
                return value
            else:
                self._misses += 1
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        async with self._lock:
            # Estimate size
            try:
                serialized = pickle.dumps(value)
                size = len(serialized)
            except:
                # Fallback to string length estimate
                size = len(str(value))

            # Check if we need to evict
            while self._current_size_bytes + size > self._max_size_bytes and self._cache:
                # Evict least recently used
                evict_key, (evict_value, evict_size, evict_ts) = self._cache.popitem(last=False)
                self._current_size_bytes -= evict_size
                self._evictions += 1

            # Add new entry
            timestamp = time.time()
            if ttl:
                timestamp += ttl  # Store expiration time

            self._cache[key] = (value, size, timestamp)
            self._current_size_bytes += size

    async def delete(self, key: str):
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                value, size, timestamp = self._cache.pop(key)
                self._current_size_bytes -= size

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._current_size_bytes = 0

    async def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "entries": len(self._cache),
            "size_mb": round(self._current_size_bytes / 1024 / 1024, 2),
            "max_size_mb": round(self._max_size_bytes / 1024 / 1024, 2),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self._evictions,
        }


class DiskCache:
    """Disk-based cache using diskcache library."""

    def __init__(self, cache_dir: str = "/root/aurora_pro/cache"):
        self._cache_dir = cache_dir
        self._cache = None
        self._available = False

        # Create cache directory
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

    async def start(self):
        """Initialize disk cache."""
        try:
            import diskcache
            self._cache = diskcache.Cache(self._cache_dir)
            self._available = True
            logger.info(f"Disk cache initialized at {self._cache_dir}")
        except ImportError:
            logger.warning("diskcache not available - disk caching disabled")
            self._available = False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        if not self._available or not self._cache:
            return None

        try:
            return self._cache.get(key)
        except Exception as e:
            logger.error(f"Disk cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in disk cache."""
        if not self._available or not self._cache:
            return

        try:
            if ttl:
                self._cache.set(key, value, expire=ttl)
            else:
                self._cache.set(key, value)
        except Exception as e:
            logger.error(f"Disk cache set error: {e}")

    async def delete(self, key: str):
        """Delete key from disk cache."""
        if not self._available or not self._cache:
            return

        try:
            self._cache.delete(key)
        except Exception as e:
            logger.error(f"Disk cache delete error: {e}")

    async def clear(self):
        """Clear all disk cache entries."""
        if not self._available or not self._cache:
            return

        try:
            self._cache.clear()
        except Exception as e:
            logger.error(f"Disk cache clear error: {e}")

    async def get_stats(self) -> Dict:
        """Get disk cache statistics."""
        if not self._available or not self._cache:
            return {"available": False}

        try:
            return {
                "available": True,
                "directory": self._cache_dir,
                "size": len(self._cache),
                "volume_path": self._cache.directory,
            }
        except Exception as e:
            logger.error(f"Disk cache stats error: {e}")
            return {"available": False, "error": str(e)}


class RedisCache:
    """Redis-based cache (optional)."""

    def __init__(self, redis_url: Optional[str] = None):
        self._redis_url = redis_url or "redis://localhost:6379"
        self._redis = None
        self._available = False

    async def start(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            self._redis = await redis.from_url(self._redis_url, decode_responses=False)
            # Test connection
            await self._redis.ping()
            self._available = True
            logger.info(f"Redis cache connected to {self._redis_url}")
        except ImportError:
            logger.warning("redis not available - Redis caching disabled")
            self._available = False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._available = False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self._available or not self._redis:
            return None

        try:
            data = await self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis."""
        if not self._available or not self._redis:
            return

        try:
            data = pickle.dumps(value)
            if ttl:
                await self._redis.setex(key, ttl, data)
            else:
                await self._redis.set(key, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str):
        """Delete key from Redis."""
        if not self._available or not self._redis:
            return

        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    async def clear(self):
        """Clear all Redis keys (dangerous!)."""
        if not self._available or not self._redis:
            return

        try:
            await self._redis.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def get_stats(self) -> Dict:
        """Get Redis statistics."""
        if not self._available or not self._redis:
            return {"available": False}

        try:
            info = await self._redis.info()
            return {
                "available": True,
                "url": self._redis_url,
                "used_memory_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"available": False, "error": str(e)}


class CacheManager:
    """
    Advanced multi-tier caching system.

    Features:
    - L1: Memory cache (8GB max, LRU eviction)
    - L2: Disk cache (diskcache)
    - L3: Redis cache (optional)
    - Automatic tier fallback
    - Cache invalidation strategies
    - Performance statistics
    """

    AUDIT_LOG_PATH = "/root/aurora_pro/logs/cache_manager.log"
    DEFAULT_MEMORY_SIZE_MB = 2048  # 2GB default for memory cache
    DEFAULT_TTL = 3600  # 1 hour

    def __init__(
        self,
        memory_size_mb: int = DEFAULT_MEMORY_SIZE_MB,
        cache_dir: str = "/root/aurora_pro/cache",
        redis_url: Optional[str] = None,
    ):
        self._memory_cache = MemoryCache(max_size_mb=memory_size_mb)
        self._disk_cache = DiskCache(cache_dir=cache_dir)
        self._redis_cache = RedisCache(redis_url=redis_url)
        self._running = False

    async def start(self):
        """Initialize all cache tiers."""
        self._running = True
        await self._disk_cache.start()
        await self._redis_cache.start()
        await self._audit_log("system", "Cache manager started")
        logger.info("Cache manager started")

    async def stop(self):
        """Shutdown cache manager."""
        self._running = False
        await self._audit_log("system", "Cache manager stopped")
        logger.info("Cache manager stopped")

    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace."""
        return f"{namespace}:{key}"

    async def get(
        self,
        namespace: str,
        key: str,
    ) -> Tuple[Optional[Any], str]:
        """
        Get value from cache (tries all tiers).

        Returns:
            (value, tier) where tier is 'memory', 'disk', 'redis', or 'miss'
        """
        cache_key = self._generate_key(namespace, key)

        # Try memory cache
        value = await self._memory_cache.get(cache_key)
        if value is not None:
            return (value, 'memory')

        # Try disk cache
        value = await self._disk_cache.get(cache_key)
        if value is not None:
            # Promote to memory cache
            await self._memory_cache.set(cache_key, value)
            return (value, 'disk')

        # Try Redis cache
        value = await self._redis_cache.get(cache_key)
        if value is not None:
            # Promote to memory and disk cache
            await self._memory_cache.set(cache_key, value)
            await self._disk_cache.set(cache_key, value)
            return (value, 'redis')

        return (None, 'miss')

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tiers: Optional[list] = None,
    ):
        """
        Set value in cache.

        Args:
            namespace: Cache namespace
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            tiers: List of tiers to use ['memory', 'disk', 'redis'] (None = all)
        """
        cache_key = self._generate_key(namespace, key)
        tiers = tiers or ['memory', 'disk', 'redis']

        if 'memory' in tiers:
            await self._memory_cache.set(cache_key, value, ttl=ttl)

        if 'disk' in tiers:
            await self._disk_cache.set(cache_key, value, ttl=ttl)

        if 'redis' in tiers:
            await self._redis_cache.set(cache_key, value, ttl=ttl)

    async def delete(self, namespace: str, key: str):
        """Delete key from all cache tiers."""
        cache_key = self._generate_key(namespace, key)

        await self._memory_cache.delete(cache_key)
        await self._disk_cache.delete(cache_key)
        await self._redis_cache.delete(cache_key)

    async def clear_namespace(self, namespace: str):
        """Clear all keys in a namespace (expensive operation)."""
        # This is a simple implementation - for production, use key prefixes
        logger.warning(f"Clearing namespace {namespace} - this clears ALL cache")
        await self._memory_cache.clear()
        await self._disk_cache.clear()
        # Don't clear Redis by default (may have other data)

    async def clear_all(self):
        """Clear all cache tiers."""
        await self._memory_cache.clear()
        await self._disk_cache.clear()
        await self._redis_cache.clear()
        await self._audit_log("clear_all", "All cache tiers cleared")

    async def get_statistics(self) -> Dict:
        """Get comprehensive cache statistics."""
        memory_stats = await self._memory_cache.get_stats()
        disk_stats = await self._disk_cache.get_stats()
        redis_stats = await self._redis_cache.get_stats()

        return {
            "memory": memory_stats,
            "disk": disk_stats,
            "redis": redis_stats,
        }

    def get_status(self) -> Dict:
        """Get cache manager status."""
        return {
            "running": self._running,
            "memory_available": True,
            "disk_available": self._disk_cache._available,
            "redis_available": self._redis_cache._available,
        }

    async def _audit_log(self, action: str, message: str, metadata: Optional[Dict] = None):
        """Write audit log entry."""
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

        entry = {
            "timestamp": timestamp,
            "action": action,
            "message": message,
            "metadata": metadata or {},
        }

        line = json.dumps(entry) + "\n"

        log_path = Path(self.AUDIT_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            async with aiofiles.open(self.AUDIT_LOG_PATH, "a") as f:
                await f.write(line)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Singleton instance
_cache_manager_instance: Optional[CacheManager] = None


def get_cache_manager(
    memory_size_mb: int = CacheManager.DEFAULT_MEMORY_SIZE_MB,
    cache_dir: str = "/root/aurora_pro/cache",
    redis_url: Optional[str] = None,
) -> CacheManager:
    """Get or create cache manager singleton."""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(
            memory_size_mb=memory_size_mb,
            cache_dir=cache_dir,
            redis_url=redis_url,
        )
    return _cache_manager_instance


__all__ = ["CacheManager", "get_cache_manager", "MemoryCache", "DiskCache", "RedisCache"]