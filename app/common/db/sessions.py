import sys
import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from config.config import settings

logger = logging.getLogger("app.db")

# Global session engine + factory
engine = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


# ---------------------------------------------------------
# Convert sync DB URLs → async DB URLs
# ---------------------------------------------------------
def _normalize_db_url_for_async(url: str) -> str:
    parsed = make_url(url)
    driver = parsed.get_driver_name()

    if "+" in driver:  # Already async
        return url

    match parsed.drivername:
        case "postgresql" | "postgres":
            return str(parsed.set(drivername="postgresql+asyncpg"))
        case "mysql":
            return str(parsed.set(drivername="mysql+aiomysql"))
        case "mssql":
            return str(parsed.set(drivername="mssql+aioodbc"))
        case "sqlite":
            if parsed.database in (None, "", ":memory:"):
                return "sqlite+aiosqlite:///:memory:"
            return str(parsed.set(drivername="sqlite+aiosqlite"))
        case _:
            return url


# ---------------------------------------------------------
# Initialize DB engine (called on startup)
# ---------------------------------------------------------
async def init_db(app=None, echo: bool | None = None):
    global engine, AsyncSessionLocal

    if engine is not None:
        logger.warning("DB engine already initialized.")
        return

    db_url = settings.DATABASE_URL
    if not db_url:
        logger.warning("No DATABASE_URL set — skipping DB initialization.")
        return

    db_url = _normalize_db_url_for_async(db_url)

    if "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    logger.info(f"Initializing DB engine: {db_url}")

    engine = create_async_engine(
        db_url,
        echo=(echo if echo is not None else settings.DB_ECHO),
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession
    )

    # REGISTER INTO app.state
    if app is not None:
        app.state.db_engine = engine
        app.state.db_sessionmaker = AsyncSessionLocal

    # Test connection
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda *_: None)
        logger.info("Database connection OK.")
    except Exception as e:
        logger.exception("Failed connecting to DB.")
        await asyncio.sleep(0.3)
        sys.exit(1)


# ---------------------------------------------------------
# Shutdown engine (called on shutdown)
# ---------------------------------------------------------
async def close_db():
    global engine, AsyncSessionLocal

    if engine:
        logger.info("Shutting down database engine...")
        await engine.dispose()
        logger.info("DB engine closed.")

    engine = None
    AsyncSessionLocal = None


# ---------------------------------------------------------
# DB Dependency for FastAPI
# ---------------------------------------------------------
# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     if not AsyncSessionLocal:
#         raise RuntimeError("DB not initialized — call init_db() first.")
#
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if not AsyncSessionLocal:
        raise RuntimeError("DB not initialized — call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
