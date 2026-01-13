# app/common/db/shared_bridge.py
"""
Bridge existing sessions.py and shared library
"""
import sys
import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, Integer, DateTime, event
from datetime import datetime
import os
import re

from .sessions import AsyncSessionLocal, engine
from config.config import settings

logger = logging.getLogger("app.db.shared")


# ---------------------------------------------------------
# Schema Management
# ---------------------------------------------------------
class SchemaManager:
    """Manages PostgreSQL schemas for multi-tenancy"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.tenants: Dict[str, str] = {}
        self.default_schema = "public"

    async def initialize(self):
        """Load tenant catalog from database"""
        await self._load_tenant_catalog()
        logger.info(f"SchemaManager initialized with {len(self.tenants)} tenants")

    async def _load_tenant_catalog(self):
        """Load tenant catalog from public.tenants table"""
        try:
            async with self.db_session_factory() as session:
                # First, ensure we're in public schema
                await session.execute("SET search_path TO public")

                # Query tenants table
                result = await session.execute(
                    "SELECT subdomain_id, schema_name FROM public.tenants WHERE status = 'active'"
                )
                rows = result.fetchall()

                self.tenants = {row[0]: row[1] for row in rows}
                logger.debug(f"Loaded tenant catalog: {self.tenants}")

        except Exception as e:
            logger.error(f"Failed to load tenant catalog: {e}")
            self.tenants = {}

    async def get_tenant_schema(self, subdomain: str) -> Optional[str]:
        """Get schema name for a tenant subdomain"""
        return self.tenants.get(subdomain)

    async def set_schema_from_subdomain(self, subdomain: str, session: AsyncSession) -> str:
        """Set schema based on subdomain (like your Yii2 implementation)"""
        schema_name = await self.get_tenant_schema(subdomain)

        if not schema_name:
            # Use default schema if tenant not found
            schema_name = self.default_schema
            logger.warning(f"Tenant not found for subdomain {subdomain}, using default schema")

        await session.execute(f"SET search_path TO {schema_name}, public")
        logger.debug(f"Schema set to: {schema_name} for subdomain: {subdomain}")
        return schema_name

    async def switch_schema(self, session: AsyncSession, schema_name: str) -> None:
        """Switch to a specific schema"""
        if not self._is_valid_schema_name(schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")

        await session.execute(f"SET search_path TO {schema_name}, public")
        logger.debug(f"Schema switched to: {schema_name}")

    def _is_valid_schema_name(self, schema_name: str) -> bool:
        """Validate schema name (PostgreSQL naming rules)"""
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, schema_name))

    async def create_schema(self, schema_name: str) -> bool:
        """Create a new schema"""
        if not self._is_valid_schema_name(schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")

        try:
            async with self.db_session_factory() as session:
                await session.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                await session.commit()
                logger.info(f"Schema created: {schema_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {e}")
            return False


# ---------------------------------------------------------
# Service-aware base models
# ---------------------------------------------------------
def get_base_model(schema: Optional[str] = None):
    """Factory function to create base models with schema support"""

    class CustomBase:
        """Base class for all models with schema support"""

        @declared_attr
        def __table_args__(cls):
            """Set schema for tables"""
            # Use provided schema, or SERVICE_SCHEMA env, or default to 'public'
            table_schema = schema or os.getenv("SERVICE_SCHEMA", "public")
            return {'schema': table_schema}

        @declared_attr
        def __tablename__(cls):
            return cls.__name__.lower()

        id = Column(Integer, primary_key=True, index=True)
        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow, nullable=False)

    return declarative_base(cls=CustomBase)


# Create base models for different schemas
ServiceBase = get_base_model()  # Uses SERVICE_SCHEMA env var
PublicBase = get_base_model("public")  # Always uses public schema


# ---------------------------------------------------------
# Enhanced get_db with schema support
# ---------------------------------------------------------
async def get_db_with_schema(
        request=None,
        schema_name: Optional[str] = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Enhanced database dependency with schema support

    Usage:
        # In FastAPI endpoint
        db = Depends(get_db_with_schema)

        # With specific schema
        db = Depends(lambda: get_db_with_schema(schema_name="tenant1"))
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized — call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            # Apply schema if requested
            if schema_name:
                manager = SchemaManager(AsyncSessionLocal)
                await manager.switch_schema(session, schema_name)
            elif request:
                # Auto-detect schema from request
                manager = SchemaManager(AsyncSessionLocal)
                await manager.initialize()

                # Extract subdomain from request
                host = request.headers.get("host", "")
                subdomain = host.split(".")[0] if "." in host else "default"

                await manager.set_schema_from_subdomain(subdomain, session)

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------
# Context manager for schema switching
# ---------------------------------------------------------
@asynccontextmanager
async def with_schema(schema_name: str):
    """
    Context manager for temporary schema switching

    Usage:
        async with with_schema("tenant1") as session:
            result = await session.execute(...)
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized — call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            manager = SchemaManager(AsyncSessionLocal)
            await manager.switch_schema(session, schema_name)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Global schema manager instance
schema_manager = SchemaManager(AsyncSessionLocal)


# ---------------------------------------------------------
# Initialize schema-aware database
# ---------------------------------------------------------
async def init_db_with_schema(app=None):
    """Initialize database with schema support"""
    from .sessions import init_db as base_init_db

    # Call your existing init_db
    await base_init_db(app)

    # Initialize schema manager
    await schema_manager.initialize()

    # Store in app state
    if app:
        app.state.schema_manager = schema_manager

    logger.info("Database initialized with schema support")