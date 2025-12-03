# app/core/cache_invalidate.py
from app.core.cache_utils import delete_cache

async def invalidate_user_cache(user_id: int):
    await delete_cache(f"user:{user_id}")
