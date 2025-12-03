import asyncio
import json
import logging
from config.config import settings  
from .manager import manager  # the WebSocketManager instance in routes
try:
    import aioredis
except Exception:
    aioredis = None

logger = logging.getLogger("ws.redis")


class RedisPubSub:
    def __init__(self):
        self.redis = None
        self.sub = None
        self.task = None

    async def connect(self):
        if not aioredis:
            logger.warning("aioredis not installed; Redis pub/sub disabled")
            return
        self.redis = aioredis.from_url(settings.REDIS_URL)
        self.sub = self.redis.pubsub()
        await self.sub.subscribe("ws-broadcast")
        self.task = asyncio.create_task(self.reader())

    async def reader(self):
        async for msg in self.sub.listen():
            if msg is None:
                continue
            if msg.get("type") == "message":
                try:
                    payload = json.loads(msg.get("data"))
                    channel = payload.get("channel")
                    await manager.broadcast(payload, channel=channel)
                except Exception:
                    logger.exception("Failed to handle pubsub message")

    async def publish(self, payload: dict):
        if not self.redis:
            return
        await self.redis.publish("ws-broadcast", json.dumps(payload))

    async def disconnect(self):
        """Gracefully close Redis and cancel background reader."""
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.sub:
            try:
                await self.sub.unsubscribe("ws-broadcast")
            except Exception:
                pass

        if self.redis:
            await self.redis.close()
            logger.info("[cache] Redis client closed")

        self.redis = None
        self.sub = None
        self.task = None


redis_pubsub = RedisPubSub()
