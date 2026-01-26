"""
Shared PostgreSQL integration runtime used by generated modules.

This module centralises SQLAlchemy engine configuration, FastAPI dependencies,
health checks, and utility helpers. Generated projects import from this module
instead of duplicating runtime logic under ``src/core``.
"""

from __future__ import annotations

import sys as _sys
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator, List

from core.settings import settings  # type: ignore[import-not-found]
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..logging import get_logger

# ========== SQLAlchemy Base ==========
Base = declarative_base()

# ========== Logging ==========
logger = get_logger(__name__)

# ========== Engine Configuration ==========
engine_config = {
    "echo": settings.DB_ECHO,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
    "pool_recycle": settings.DB_POOL_RECYCLE,
    "pool_timeout": settings.DB_POOL_TIMEOUT,
}

# ========== Async Engine ==========
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    future=True,
    **engine_config,
)

# ========== Sync Engine ==========
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    future=True,
    **engine_config,
)

# ========== Test Engines (Optional) ==========
test_database_url = getattr(settings, "TEST_DATABASE_URL", None) or getattr(
    settings, "test_database_url", None
)

if test_database_url:
    test_async_engine = create_async_engine(
        test_database_url.replace("postgresql://", "postgresql+asyncpg://"),
        future=True,
        **engine_config,
    )
    test_sync_engine = create_engine(
        test_database_url.replace("postgresql://", "postgresql+psycopg://"),
        future=True,
        **engine_config,
    )
else:
    test_async_engine = None
    test_sync_engine = None

# ========== Session Makers ==========
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# ========== Test Session Makers (Optional) ==========
TestAsyncSessionLocal = (
    async_sessionmaker(
        bind=test_async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    if test_database_url and test_async_engine
    else None
)

TestSyncSessionLocal = (
    sessionmaker(
        bind=test_sync_engine,
        autocommit=False,
        autoflush=False,
    )
    if test_database_url and test_sync_engine
    else None
)


# ========== FastAPI Dependency Injection ==========
async def get_postgres_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async PostgreSQL database session."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db() -> Generator[Session, None, None]:
    """Dependency for sync PostgreSQL database session."""

    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ========== Transaction Context Managers ==========
@asynccontextmanager
async def transactional_async() -> AsyncGenerator[AsyncSession, None]:
    """Async transaction context manager with automatic commit/rollback."""

    async with AsyncSessionLocal() as session, session.begin():
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@contextmanager
def transactional_sync() -> Generator[Session, None, None]:
    """Sync transaction context manager with automatic commit/rollback."""

    session = SyncSessionLocal()
    try:
        with session.begin():
            try:
                yield session
            except Exception:
                session.rollback()
                raise
    finally:
        session.close()


# ========== Health Checks ==========
async def check_postgres_connection() -> None:
    """Check async PostgreSQL connection health."""

    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL async connection is active")
    except SQLAlchemyError as exc:
        logger.error(f"❌ Async DB connection failed: {exc}")
        raise HTTPException(status_code=500, detail="Async DB connection failed") from exc


def check_postgres_connection_sync() -> None:
    """Check sync PostgreSQL connection health."""

    try:
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL sync connection is active")
    except SQLAlchemyError as exc:
        logger.error(f"❌ Sync DB connection failed: {exc}")
        raise HTTPException(status_code=500, detail="Sync DB connection failed") from exc


async def get_pool_status() -> dict:
    """Get current connection pool status."""

    pool = async_engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }


# ========== Lifecycle Management ==========
async def close_async_engine() -> None:
    """Close async engine and dispose of connection pool."""

    await async_engine.dispose()
    logger.info("🧹 Async PostgreSQL engine disposed")


def close_sync_engine() -> None:
    """Close sync engine and dispose of connection pool."""

    sync_engine.dispose()
    logger.info("🧹 Sync PostgreSQL engine disposed")


async def initialize_database() -> None:
    """Initialise database (create tables, etc.)."""

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database initialized")


# ========== Utilities ==========
async def execute_raw_sql(sql: str) -> List[Any]:
    """Execute raw SQL query (use with caution)."""

    async with AsyncSessionLocal() as session:
        result = await session.execute(text(sql))
        rows = result.fetchall()
        return list(rows)


def get_database_url(hide_password: bool = True) -> str:
    """Get database URL with optional password masking."""

    url = str(settings.DATABASE_URL)
    if hide_password and "@" in url:
        parts = url.split("@")
        credentials = parts[0].split("://")[1]
        if ":" in credentials:
            user = credentials.split(":")[0]
            url = url.replace(credentials, f"{user}:***")
    return url


__all__ = [
    "AsyncSessionLocal",
    "AsyncSession",
    "Base",
    "TestAsyncSessionLocal",
    "TestSyncSessionLocal",
    "async_engine",
    "check_postgres_connection",
    "check_postgres_connection_sync",
    "close_async_engine",
    "close_sync_engine",
    "execute_raw_sql",
    "get_database_url",
    "get_postgres_db",
    "get_pool_status",
    "get_sync_db",
    "initialize_database",
    "logger",
    "sync_engine",
    "transactional_async",
    "transactional_sync",
]

_sys.modules.setdefault("src.core.database.postgres", _sys.modules[__name__])
_sys.modules.setdefault("core.database.postgres", _sys.modules[__name__])
