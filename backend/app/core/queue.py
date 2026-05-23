"""Redis-backed job queue using arq.

Producers call `enqueue(job_name, payload)`. Workers in
`app.workers.pipeline_worker` consume by job name.
"""
from typing import Any
from arq.connections import RedisSettings, create_pool
from app.config import settings

_pool = None


async def init_queue():
    global _pool
    _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))


async def enqueue(job_name: str, payload: dict[str, Any]):
    if _pool is None:
        await init_queue()
    await _pool.enqueue_job(job_name, payload)
