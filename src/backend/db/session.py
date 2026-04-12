"""
Scout — Database Session Management

Provides two session factories:
  1. Async (AsyncSession) — used by FastAPI route handlers via Depends()
  2. Sync (Session)       — used by the LangGraph agent pipeline

Both derive from the same DATABASE_URL environment variable.
"""

import os
from contextlib import contextmanager
from typing import AsyncGenerator, Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Derive sync URL from the async one (replace asyncpg driver with psycopg2)
# Also fix SSL param: asyncpg uses "ssl=require", psycopg2 uses "sslmode=require"
SYNC_DATABASE_URL = (
    DATABASE_URL.replace("+asyncpg", "+psycopg2").replace("?ssl=require", "?sslmode=require").replace("&ssl=require", "&sslmode=require")
    if DATABASE_URL else ""
)

# ---------------------------------------------------------------------------
# Async engine — for FastAPI route handlers
# ---------------------------------------------------------------------------
async_engine = (
    create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    if DATABASE_URL
    else None
)

AsyncSessionLocal = (
    async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    if async_engine
    else None
)

# ---------------------------------------------------------------------------
# Sync engine — for agent pipeline (Person 1's code)
# ---------------------------------------------------------------------------
sync_engine = (
    create_engine(SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
    if SYNC_DATABASE_URL
    else None
)

SyncSessionLocal = sessionmaker(bind=sync_engine) if sync_engine else None


# ---------------------------------------------------------------------------
# Dependency: async session generator for FastAPI Depends()
# ---------------------------------------------------------------------------
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for use in FastAPI route handlers."""
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in .env or environment variables."
        )
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Context manager: sync session for the agent pipeline
# ---------------------------------------------------------------------------
@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """
    Provide a sync database session with auto-commit/rollback semantics.
    Used by Person 1's agents that call pipeline.invoke() synchronously.
    """
    if SyncSessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in .env or environment variables."
        )
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
