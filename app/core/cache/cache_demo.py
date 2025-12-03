from fastapi import APIRouter
from fastapi_cache.decorator import cache
from app.common.cache.cache_utils import get_cache, set_cache

router = APIRouter(prefix="/cache", tags=["CacheDemo"])

@router.get("/decorated")
@cache(expire=30)     # response cached for 30s
async def get_cached_items():
    # heavy/computation or DB call simulated
    return {"message": "fresh data", "value": 123}

@router.get("/manual-set")
async def manual_set(key: str, value: str):
    await set_cache(key, value, expire=120)
    return {"status": "ok", "key": key, "value": value}

@router.get("/manual-get")
async def manual_get(key: str):
    v = await get_cache(key)
    return {"key": key, "value": v}
