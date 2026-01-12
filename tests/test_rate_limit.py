import pytest
import asyncio
from fastapi import FastAPI, Depends
from starlette.testclient import TestClient
import aioredis
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter import FastAPILimiter

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module", autouse=True)
async def redis_setup():
    redis = await aioredis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis)
    yield
    await redis.flushall()
    await redis.close()

def test_rate_limit_local():
    app = FastAPI()

    @app.get("/rl", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
    async def rl():
        return {"ok": True}

    client = TestClient(app)
    r1 = client.get("/rl"); assert r1.status_code == 200
    r2 = client.get("/rl"); assert r2.status_code == 200
    r3 = client.get("/rl"); assert r3.status_code == 429
