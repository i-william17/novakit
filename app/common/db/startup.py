# app/db/startup.py
import os
import asyncio
import logging
from alembic import command
from alembic.config import Config
from shared.database.connection import get_db_engine

logger = logging.getLogger(__name__)


def run_migrations():
    """Run Alembic migrations"""
    alembic_cfg = Config("alembic.ini")

    # Get service schema from environment
    schema = os.getenv("SERVICE_SCHEMA", "public")

    # Set target schema in Alembic config
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
    alembic_cfg.set_main_option("version_locations", f"alembic/versions/{schema}")

    # Run migrations
    command.upgrade(alembic_cfg, "head")
    logger.info(f"Migrations applied for schema: {schema}")


async def initialize_database_on_startup():
    """Initialize database when service starts"""
    try:
        # Wait for database to be ready
        engine = get_db_engine()
        async with engine.begin() as conn:
            # Create schema if it doesn't exist
            schema = os.getenv("SERVICE_SCHEMA", "public")
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

            # Set search path
            await conn.execute(f"SET search_path TO {schema}, public")

        # Run migrations
        await asyncio.to_thread(run_migrations)

        logger.info("Database initialization completed")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise