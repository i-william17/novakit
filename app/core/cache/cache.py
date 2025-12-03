from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from redis import asyncio as aioredis
from config.config import settings  
import logging
from typing import Optional

log = logging.getLogger("app.cache")

# store redis client so it can be closed on shutdown
_redis_client: Optional[aioredis.Redis] = None

async def init_cache():
    """
    Initialize FastAPI cache backend according to settings.
    Supports:
      - redis backend (default)
      - in-memory (useful for testing or when Redis disabled)
    """
    global _redis_client

    backend = settings.CACHE_BACKEND.lower() if settings.CACHE_BACKEND else "redis"

    if backend == "redis" and settings.ENABLE_REDIS_CACHE and settings.REDIS_URL:
        try:
            _redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
            await _redis_client.ping()  # quick check
            FastAPICache.init(RedisBackend(_redis_client), prefix=settings.FASTAPI_CACHE_PREFIX)
            log.info("[cache] Redis cache initialized")
        except Exception as e:
            log.exception("[cache] Redis init failed, falling back to InMemoryBackend: %s", e)
            FastAPICache.init(InMemoryBackend(), prefix=settings.FASTAPI_CACHE_PREFIX)
    else:
        log.info("[cache] Using InMemoryBackend for caching")
        FastAPICache.init(InMemoryBackend(), prefix=settings.FASTAPI_CACHE_PREFIX)


async def close_cache():
    """Close underlying redis connection if present (call on shutdown)."""
    global _redis_client
    try:
        if _redis_client:
            await _redis_client.close()
            log.info("[cache] Redis client closed")
    except Exception:
        log.exception("[cache] Error closing redis client")
