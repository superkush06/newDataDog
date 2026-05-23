"""Postgres connection pool (asyncpg)."""
import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(
        settings.database_url, min_size=2, max_size=10,
    )


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


class _PoolProxy:
    """Forwards attribute access to the live pool, so callers that did
    `from app.core.db import pool` still see the current pool after init."""

    def __getattr__(self, name: str):
        if _pool is None:
            raise RuntimeError(
                "Postgres pool not initialized; call init_pool() at app startup."
            )
        return getattr(_pool, name)

    def __bool__(self) -> bool:
        return _pool is not None


pool = _PoolProxy()
