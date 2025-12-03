import asyncio
import logging

# from config.config import settings  
from app.core.logging.logging_config import setup_logging
from app.core.cache.cache import init_cache, close_cache
from app.ws.redis_pubsub import redis_pubsub
from app.common.db.sessions import init_db, close_db


logger = logging.getLogger("app.kernel")

# Initialize logging early
setup_logging()


# --- PERIODIC TASKS ---
async def periodic_broadcast():
    """Broadcasts heartbeat events periodically."""
    # WebSocket manager
    # from app.modules.agent.endpoints.WebSocketEndpoint import endpoint as ws_endpoint

    # manager = ws_endpoint.manager  # get the WebSocketManager instance

    logger.info("Periodic broadcast task started.")
    while True:
        try:
            payload = {"event": "heartbeat", "payload": {"text": "server heartbeat"}}

            if redis_pubsub.redis:
                await redis_pubsub.publish(payload)
                logger.debug("Heartbeat published to Redis.")
            else:
                #await manager.broadcast(payload)
                logger.debug("Heartbeat broadcasted via WebSocket manager.")
        except Exception:
            logger.exception("Periodic broadcast failed")
        await asyncio.sleep(10)  # every 10 seconds



# --- BOOTSTRAP METHOD ---
async def boot(app):
    """
    Bootstraps Cypher Server subsystems (cache, redis, tasks, etc.)
    Called once from main.py after FastAPI app is created.
    """
    logger.info("Bootstrapping Cypher Server subsystems...")
    
    await init_db()  
    
    await init_cache()
    await redis_pubsub.connect()
    asyncio.create_task(periodic_broadcast())

    # Register shutdown cleanup
    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Shutting down subsystems...")
        await close_db()
        await close_cache()
        await redis_pubsub.disconnect()
        logger.info("All subsystems shut down cleanly.")

    logger.info("Kernel bootstrapped and ready.")

