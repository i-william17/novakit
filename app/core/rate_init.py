import aioredis
import logging
from fastapi import FastAPI

logger = logging.getLogger("novakit.rate")

async def init_rate_limiters(app: FastAPI, redis_url: str, fastapi_limiter=None):
    """
    Initialize fastapi-limiter and slowapi limiter (optional).
    """
    # fastapi-limiter
    try:
        from fastapi_limiter import FastAPILimiter
        # aioredis.create_redis_pool uses different API depending on aioredis version.
        # fastapi-limiter expects aioredis connection pool instance.
        redis = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis)
        app.state._fastapi_limiter_redis = redis
        logger.info("fastapi-limiter initialized")
    except Exception:
        logger.exception("fastapi-limiter initialization failed")

    # slowapi - optional, for decorator style
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        from slowapi.middleware import SlowAPIMiddleware
        # create limiter; can back to redis via storage arg in limits if desired
        limiter = Limiter(key_func=get_remote_address)
        app.state.slowapi_limiter = limiter
        app.add_middleware(SlowAPIMiddleware, limiter=limiter)
        logger.info("slowapi limiter initialized (middleware)")
    except Exception:
        logger.exception("slowapi init failed (optional)")
