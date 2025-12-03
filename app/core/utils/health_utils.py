import asyncio
import aio_pika
from sqlalchemy import text
from config.config import settings  
from app.common.db import sessions


import logging

logger = logging.getLogger("app.health")

async def check_postgres_connection() -> bool:
    """Check PostgreSQL connection using current async engine."""
    try:
        engine = sessions.engine  # always get fresh global reference
        if not engine:
            logger.warning("[DB Health Warning] Engine not initialized at check time.")
            return False

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("[DB Health Error] %s", e)
        return False


async def check_rabbitmq_connection() -> bool:
    """Check RabbitMQ connection."""
    try:
        connection = await aio_pika.connect_robust(
            host=settings.BROKER_HOST,
            port=int(settings.BROKER_PORT),
            virtualhost=settings.BROKER_VHOST,
            login=settings.BROKER_USERNAME,
            password=settings.BROKER_PASSWORD,
        )
        await connection.close()
        return True
    except Exception as e:
        print(f"[RabbitMQ Health Error] {e}")
        return False


async def run_health_checks():
    """Run all health checks concurrently."""
    postgres_ok, rabbit_ok = await asyncio.gather(
        check_postgres_connection(),
        check_rabbitmq_connection(),
    )

    status = {
        "database": "healthy" if postgres_ok else "unhealthy",
        "broker": "healthy" if rabbit_ok else "unhealthy",
    }
    
    logger.info("Health check result: %s", status)
    return status
