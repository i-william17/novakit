from fastapi_cache import FastAPICache
from typing import Any

async def get_cache(key: str) -> Any:
    backend = FastAPICache.get_backend()
    # most backends provide async get
    return await backend.get(key)

async def set_cache(key: str, value: Any, expire: int = 60):
    backend = FastAPICache.get_backend()
    return await backend.set(key, value, expire=expire)

async def delete_cache(key: str):
    backend = FastAPICache.get_backend()
    # some backends call delete / expire — RedisBackend exposes delete
    if hasattr(backend, "delete"):
        return await backend.delete(key)
    return None
