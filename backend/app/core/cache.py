"""Redis caching layer for News Tunneler."""
import json
import hashlib
from functools import wraps
from typing import Any, Callable, Optional
from redis import Redis, ConnectionError as RedisConnectionError
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

# Initialize Redis client
redis_client: Optional[Redis] = None

def get_redis_client() -> Optional[Redis]:
    """Get Redis client with lazy initialization."""
    global redis_client
    
    if not settings.redis_enabled:
        return None
    
    if redis_client is None:
        try:
            redis_client = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            redis_client.ping()
            logger.info(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")
        except (RedisConnectionError, Exception) as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Caching disabled.")
            redis_client = None
    
    return redis_client


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """
    Cache function results in Redis.
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key (default: function name)
    
    Usage:
        @cache_result(ttl=60, key_prefix="prices")
        def get_price(symbol: str):
            return expensive_api_call(symbol)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            client = get_redis_client()
            
            # If Redis is not available, execute function normally
            if client is None:
                return func(*args, **kwargs)
            
            # Create cache key from function name and arguments
            prefix = key_prefix or func.__name__
            key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
            cache_key = f"cache:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            try:
                # Try to get from cache
                cached = client.get(cache_key)
                if cached:
                    logger.debug(f"Cache HIT: {prefix}")
                    return json.loads(cached)
                
                # Execute function and cache result
                logger.debug(f"Cache MISS: {prefix}")
                result = func(*args, **kwargs)
                
                # Cache the result
                client.setex(cache_key, ttl, json.dumps(result, default=str))
                
                return result
            except Exception as e:
                logger.warning(f"Cache error for {prefix}: {e}. Executing without cache.")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str = "*"):
    """
    Invalidate cache entries matching pattern.
    
    Args:
        pattern: Redis key pattern (default: all cache keys)
    
    Usage:
        invalidate_cache("cache:prices:*")
        invalidate_cache("cache:signals:*")
    """
    client = get_redis_client()
    if client is None:
        return
    
    try:
        full_pattern = f"cache:{pattern}" if not pattern.startswith("cache:") else pattern
        keys = client.keys(full_pattern)
        if keys:
            client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries matching '{pattern}'")
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    client = get_redis_client()
    if client is None:
        return {"status": "disabled"}
    
    try:
        info = client.info("stats")
        return {
            "status": "connected",
            "total_keys": client.dbsize(),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / 
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            ) * 100,
        }
    except Exception as e:
        logger.warning(f"Error getting cache stats: {e}")
        return {"status": "error", "error": str(e)}


def cache_set(key: str, value: Any, ttl: int = 300):
    """
    Set a value in cache.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds
    """
    client = get_redis_client()
    if client is None:
        return
    
    try:
        cache_key = f"cache:{key}"
        client.setex(cache_key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Cache set error for {key}: {e}")


def cache_get(key: str) -> Optional[Any]:
    """
    Get a value from cache.
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if not found
    """
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        cache_key = f"cache:{key}"
        cached = client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        logger.warning(f"Cache get error for {key}: {e}")
        return None


def cache_delete(key: str):
    """
    Delete a value from cache.
    
    Args:
        key: Cache key
    """
    client = get_redis_client()
    if client is None:
        return
    
    try:
        cache_key = f"cache:{key}"
        client.delete(cache_key)
    except Exception as e:
        logger.warning(f"Cache delete error for {key}: {e}")

