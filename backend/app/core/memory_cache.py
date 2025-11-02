"""
In-memory caching system for News Tunneler.

Provides fast in-memory caching with TTL as a fallback when Redis is not available.
This cache is process-local and will not be shared across workers.
"""

import time
import json
import logging
from typing import Any, Optional, Dict
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with TTL."""
    
    def __init__(self, data: Any, ttl: int):
        self.data = data
        self.timestamp = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.timestamp) > self.ttl
    
    def age(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.timestamp


class MemoryCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                logger.info(f"💾 Cache MISS: {key}")
                return None
            
            entry = self._cache[key]
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                logger.info(f"💾 Cache EXPIRED: {key} (age: {entry.age():.1f}s)")
                return None

            self._hits += 1
            logger.info(f"💾 Cache HIT: {key} (age: {entry.age():.1f}s, ttl: {entry.ttl}s)")
            return entry.data
    
    def set(self, key: str, value: Any, ttl: int):
        """Set value in cache with TTL in seconds."""
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.info(f"💾 Cache SET: {key} (ttl: {ttl}s)")
    
    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Memory cache deleted: {key}")
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info(f"Memory cache cleared: {count} entries removed")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            
            return {
                "status": "active",
                "entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.1f}%",
                "total_requests": total,
            }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Memory cache cleanup: {len(expired_keys)} expired entries removed")
            
            return len(expired_keys)


# Global cache instance
_memory_cache = MemoryCache()


# Cache TTL constants (in seconds)
TTL_MODEL_REGISTRY = 300  # 5 minutes
TTL_PREDICTION_FILES = 3600  # 1 hour (predictions don't change until next day)
TTL_OPPORTUNITIES = 60  # 1 minute
TTL_INTRADAY_DATA = 60  # 1 minute
TTL_SIGNAL_BATCH = 300  # 5 minutes


def get_memory_cache() -> MemoryCache:
    """Get global memory cache instance."""
    return _memory_cache


# Specific cache functions for common use cases

def get_model_registry_cached(registry_path: Path) -> Dict[str, Any]:
    """
    Get model registry from cache or load from file.
    
    Args:
        registry_path: Path to registry.json file
    
    Returns:
        Dictionary of model metadata
    """
    cache_key = f"model_registry:{registry_path}"
    cached_data = _memory_cache.get(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    # Load from file
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    _memory_cache.set(cache_key, data, TTL_MODEL_REGISTRY)
    logger.info(f"Loaded model registry from file: {len(data)} models")
    return data


def get_prediction_file_cached(file_path: Path) -> Any:
    """
    Get prediction file from cache or load from disk.
    
    Args:
        file_path: Path to prediction JSON file
    
    Returns:
        Parsed JSON data or None if file doesn't exist
    """
    cache_key = f"prediction_file:{file_path}"
    cached_data = _memory_cache.get(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    # Load from file
    if not file_path.exists():
        logger.warning(f"Prediction file not found: {file_path}")
        return None
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    _memory_cache.set(cache_key, data, TTL_PREDICTION_FILES)
    logger.info(f"Loaded prediction file from disk: {file_path.name} ({len(data)} items)")
    return data


def cache_signal_batch(key: str, data: Any):
    """Cache signal batch query results."""
    _memory_cache.set(f"signal_batch:{key}", data, TTL_SIGNAL_BATCH)


def get_signal_batch_cached(key: str) -> Optional[Any]:
    """Get cached signal batch query results."""
    return _memory_cache.get(f"signal_batch:{key}")


def invalidate_model_registry():
    """Invalidate model registry cache."""
    # Delete all keys that start with "model_registry:"
    with _memory_cache._lock:
        keys_to_delete = [k for k in _memory_cache._cache.keys() if k.startswith("model_registry:")]
        for key in keys_to_delete:
            del _memory_cache._cache[key]
    logger.info(f"Model registry cache invalidated: {len(keys_to_delete)} entries")


def invalidate_prediction_files(symbol: str):
    """Invalidate prediction file caches for a symbol."""
    _memory_cache.delete(f"prediction_file:backend/models/{symbol}_predict_line.json")
    _memory_cache.delete(f"prediction_file:backend/models/{symbol}_predict_signals.json")
    logger.info(f"Prediction file caches invalidated for {symbol}")


def invalidate_opportunities():
    """Invalidate opportunities cache."""
    # Delete all keys that start with "opportunities:"
    with _memory_cache._lock:
        keys_to_delete = [k for k in _memory_cache._cache.keys() if k.startswith("opportunities:")]
        for key in keys_to_delete:
            del _memory_cache._cache[key]
    logger.info(f"Opportunities cache invalidated: {len(keys_to_delete)} entries")


def invalidate_signal_batches():
    """Invalidate all signal batch caches."""
    with _memory_cache._lock:
        keys_to_delete = [k for k in _memory_cache._cache.keys() if k.startswith("signal_batch:")]
        for key in keys_to_delete:
            del _memory_cache._cache[key]
    logger.info(f"Signal batch cache invalidated: {len(keys_to_delete)} entries")


# Background cleanup
async def cache_cleanup_task():
    """Background task to cleanup expired cache entries."""
    import asyncio
    
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        removed = _memory_cache.cleanup_expired()
        if removed > 0:
            logger.info(f"Cache cleanup: removed {removed} expired entries")

