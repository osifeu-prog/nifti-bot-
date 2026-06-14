# -*- coding: utf-8 -*-
"""
SLH shared_db_core
Single source of truth for PostgreSQL connection pool.
Fail-Fast: if DB is unreachable, services crash instead of running silently.
"""

import os
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None


async def init_db_pool(database_url: Optional[str] = None) -> asyncpg.Pool:
    """Initialize the global connection pool. Idempotent. Fail-fast on error."""
    global _pool
    if _pool is not None:
        return _pool
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing - refusing to start")
    try:
        _pool = await asyncpg.create_pool(
            url,
            min_size=1,
            max_size=4,
            timeout=10,
            command_timeout=30,
        )
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        print("[DB] Pool created and verified OK")
        return _pool
    except Exception as e:
        print(f"[DB] CRITICAL: cannot connect: {e}")
        raise RuntimeError(f"DB CONNECTION FAILED: {e}")


async def get_db() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized - init_db_pool() must run at startup")
    return _pool


async def db_health() -> bool:
    if _pool is None:
        return False
    try:
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None




