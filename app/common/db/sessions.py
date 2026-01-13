import sys
import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from config.config import settings

from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime, event, MetaData
from datetime import datetime
import os

logger = logging.getLogger("app.db")

# Global session engine + factory
engine = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None
_service_schema: Optional[str] = None
_tenant_catalog: Dict[str, str] = {}


# **************************************************************************************
# ---------------------------------------------------------
# Base models with schema support
# ---------------------------------------------------------
class CustomBase:
    """Base class for all models with schema support"""

    @declared_attr
    def __table_args__(cls):
        """Set schema for tables"""
        schema = os.getenv("SERVICE_SCHEMA", "public")
        return {'schema': schema}

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)


Base = declarative_base(cls=CustomBase)


# Public schema models (for cross-service tables)
class PublicBase:
    """Base for tables in public schema"""

    @declared_attr
    def __table_args__(cls):
        return {'schema': 'public'}

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)


PublicBase = declarative_base(cls=PublicBase)
# **************************************************************************************


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
    global engine, AsyncSessionLocal, _service_schema, _tenant_catalog

    if engine is not None:
        logger.warning("DB engine already initialized.")
        return

    db_url = settings.DATABASE_URL
    if not db_url:
        logger.warning("No DATABASE_URL set — skipping DB initialization.")
        return

    db_url = _normalize_db_url_for_async(db_url)

    # **********************************************
    # Use service-specific schema
    # _service_schema = schema or os.getenv("SERVICE_SCHEMA", "public")
    # if tenant_catalog:
    #     _tenant_catalog = tenant_catalog
    #
    # logger.info(f"Initializing DB engine for schema: {_service_schema}")
    # logger.info(f"Database URL: {db_url}")
    # **********************************************


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

    # Add event listener to set search_path for each connection
    # @event.listens_for(_engine.sync_engine, "connect")
    # def set_search_path(dbapi_connection, connection_record):
    #     cursor = dbapi_connection.cursor()
    #     cursor.execute(f"SET search_path TO {_service_schema}, public")
    #     cursor.close()

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
        # app.state.service_schema = _service_schema

    # Test connection
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda *_: None)
            # Verify schema exists, create if not
            # await conn.execute(
            #     f"CREATE SCHEMA IF NOT EXISTS {_service_schema}"
            # )
            # await conn.execute(f"SET search_path TO {_service_schema}, public")
        logger.info("Database connection OK.")
        # logger.info(f"Database connection OK. Schema: {_service_schema}")
    except Exception as e:
        logger.exception("Failed connecting to DB.")
        # logger.exception(f"Failed connecting to DB with schema {_service_schema}")
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

# **********************************************************************************************************************
# ---------------------------------------------------------
# Schema switching utilities
# ---------------------------------------------------------
# class SchemaManager:
#     """Manage schema switching for multi-tenancy"""
#
#     @staticmethod
#     async def get_tenant_schema(tenant_id: str) -> Optional[str]:
#         """Get schema name for a tenant"""
#         return _tenant_catalog.get(tenant_id)
#
#     @staticmethod
#     async def create_schema(schema_name: str) -> bool:
#         """Create a new schema"""
#         if not _engine:
#             raise RuntimeError("Database not initialized")
#
#         async with _engine.begin() as conn:
#             await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
#         return True
#
#     @staticmethod
#     async def switch_schema(session: AsyncSession, schema_name: str) -> None:
#         """Switch session to different schema"""
#         await session.execute(f"SET search_path TO {schema_name}, public")
#         session.commit()  # Flush any pending changes
#
#     @staticmethod
#     @asynccontextmanager
#     async def with_schema(schema_name: str):
#         """Context manager for temporary schema switching"""
#         if not _AsyncSessionLocal:
#             raise RuntimeError("Database not initialized")
#
#         async with _AsyncSessionLocal() as session:
#             try:
#                 await session.execute(f"SET search_path TO {schema_name}, public")
#                 yield session
#                 await session.commit()
#             except Exception:
#                 await session.rollback()
#                 raise
#             finally:
#                 # Reset to service schema
#                 await session.execute(f"SET search_path TO {_service_schema}, public")
# **********************************************************************************************************************


# ---------------------------------------------------------
# DB Dependency for FastAPI
# ---------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if not AsyncSessionLocal:
        raise RuntimeError("DB not initialized — call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ---------------------------------------------------------
# DB Dependency for FastAPI with schema support
# ---------------------------------------------------------
# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     if not _AsyncSessionLocal:
#         raise RuntimeError("DB not initialized — call init_db() first.")
#
#     async with _AsyncSessionLocal() as session:
#         try:
#             # Set search_path for this session
#             await session.execute(f"SET search_path TO {_service_schema}, public")
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()
#
#
# # ---------------------------------------------------------
# # Shutdown engine
# # ---------------------------------------------------------
# async def close_db():
#     global _engine, _AsyncSessionLocal, _service_schema, _tenant_catalog
#
#     if _engine:
#         logger.info("Shutting down database engine...")
#         await _engine.dispose()
#         logger.info("DB engine closed.")
#
#     _engine = None
#     _AsyncSessionLocal = None
#     _service_schema = None
#     _tenant_catalog = {}
