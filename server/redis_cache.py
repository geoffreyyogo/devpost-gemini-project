"""
Redis caching service for Smart Shamba.

Provides a decorator-based caching layer that integrates with the FastAPI
backend. Supports TTL-based expiry, key namespacing, and graceful
degradation when Redis is unavailable.

Usage:
    cache = RedisCache()

    @cache.cached(prefix="weather", ttl=900)
    async def get_weather(county_id: str):
        ...

    # Manual operations
    await cache.set("key", data, ttl=600)
    data = await cache.get("key")
    await cache.invalidate("weather:*")
"""

import os
import json
import hashlib
import logging
import functools
from typing import Any, Optional, Callable

logger = logging.getLogger(__name__)

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.info("redis package not installed — caching disabled")


class RedisCache:
    """Redis-backed cache with graceful degradation."""

    def __init__(self, url: Optional[str] = None):
        self.enabled = False
        self._client: Optional[Any] = None

        if not REDIS_AVAILABLE:
            logger.info("RedisCache: redis package not available, running without cache")
            return

        url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self._client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=2,
                retry_on_timeout=True,
            )
            # Test the connection
            self._client.ping()
            self.enabled = True
            logger.info(f"✓ RedisCache connected: {url.split('@')[-1]}")
        except Exception as e:
            logger.warning(f"⚠ RedisCache: could not connect to Redis ({e}). Running without cache.")
            self._client = None

    # ------------------------------------------------------------------ #
    #  Core operations
    # ------------------------------------------------------------------ #

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value. Returns None on miss or error."""
        if not self.enabled:
            return None
        try:
            raw = self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:
            logger.debug(f"Cache GET error for '{key}': {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Cache a value with TTL (seconds). Returns True on success."""
        if not self.enabled:
            return False
        try:
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.debug(f"Cache SET error for '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a specific key."""
        if not self.enabled:
            return False
        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache DELETE error for '{key}': {e}")
            return False

    def invalidate(self, pattern: str) -> int:
        """Invalidate all keys matching a glob pattern (e.g. 'weather:*').
        Returns the number of keys deleted."""
        if not self.enabled:
            return 0
        try:
            keys = list(self._client.scan_iter(match=pattern, count=100))
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache INVALIDATE error for '{pattern}': {e}")
            return 0

    def stats(self) -> dict:
        """Get cache statistics for monitoring."""
        if not self.enabled:
            return {"enabled": False}
        try:
            info = self._client.info("stats")
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "connected_clients": self._client.info("clients").get("connected_clients", 0),
                "used_memory": self._client.info("memory").get("used_memory_human", "?"),
            }
        except Exception:
            return {"enabled": True, "error": "could not fetch stats"}

    # ------------------------------------------------------------------ #
    #  Key generation
    # ------------------------------------------------------------------ #

    @staticmethod
    def make_key(prefix: str, *args, **kwargs) -> str:
        """Build a deterministic cache key from prefix + arguments."""
        parts = [str(a) for a in args]
        parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
        raw = ":".join(parts)
        # Hash long keys to stay under Redis key-length limits
        if len(raw) > 100:
            raw = hashlib.md5(raw.encode()).hexdigest()
        return f"ss:{prefix}:{raw}" if raw else f"ss:{prefix}"

    # ------------------------------------------------------------------ #
    #  Decorator
    # ------------------------------------------------------------------ #

    def cached(self, prefix: str, ttl: int = 300, key_builder: Optional[Callable] = None):
        """Decorator for caching function results.

        Works with both sync and async functions. When Redis is down,
        the decorated function runs normally without caching.

        Args:
            prefix: Cache key namespace (e.g. 'weather', 'farmer')
            ttl: Time-to-live in seconds
            key_builder: Optional custom key builder fn(args, kwargs) -> str
        """
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Build key
                if key_builder:
                    cache_key = f"ss:{prefix}:{key_builder(*args, **kwargs)}"
                else:
                    # Skip 'self' argument for methods
                    fn_args = args[1:] if args and hasattr(args[0], '__class__') else args
                    cache_key = self.make_key(prefix, *fn_args, **kwargs)

                # Try cache first
                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached

                # Cache miss — call the function
                result = await func(*args, **kwargs)

                # Cache the result (skip None/error results)
                if result is not None:
                    self.set(cache_key, result, ttl)
                    logger.debug(f"Cache SET: {cache_key} (ttl={ttl}s)")

                return result

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                if key_builder:
                    cache_key = f"ss:{prefix}:{key_builder(*args, **kwargs)}"
                else:
                    fn_args = args[1:] if args and hasattr(args[0], '__class__') else args
                    cache_key = self.make_key(prefix, *fn_args, **kwargs)

                cached = self.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached

                result = func(*args, **kwargs)

                if result is not None:
                    self.set(cache_key, result, ttl)
                    logger.debug(f"Cache SET: {cache_key} (ttl={ttl}s)")

                return result

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


# ------------------------------------------------------------------ #
#  Singleton instance
# ------------------------------------------------------------------ #

_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get or create the global RedisCache instance."""
    global _instance
    if _instance is None:
        _instance = RedisCache()
    return _instance
