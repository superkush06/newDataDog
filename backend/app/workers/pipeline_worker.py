"""arq-compatible worker function surfaces."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

try:
    from arq.connections import RedisSettings
except ImportError:
    RedisSettings = None

try:
    from app.config import settings
except ImportError:
    settings = None


async def _missing(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "skipped",
        "reason": "track1_dependency_missing",
        "dependency": name,
        "payload": payload,
    }


def _redis_settings():
    if RedisSettings is None or settings is None:
        return None
    return RedisSettings.from_dsn(settings.redis_url)


async def monitor_persist(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    try:
        from app.pipeline.monitor import persist_post
        from app.models import Post
    except ImportError:
        return await _missing("app.pipeline.monitor.persist_post", payload)
    post_payload = payload.get("post", {})
    return await persist_post(payload.get("brand_id"), Post(**post_payload))


async def cluster_run(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    try:
        from app.pipeline.cluster import run_clustering
    except ImportError:
        return await _missing("app.pipeline.cluster.run_clustering", payload)
    return await run_clustering(payload.get("brand_id"))


async def score_run(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    try:
        from app.pipeline.score import run_scoring
    except ImportError:
        return await _missing("app.pipeline.score.run_scoring", payload)
    return await run_scoring(payload.get("brand_id"))


async def act_run(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    try:
        from app.pipeline.act import run_act
    except ImportError:
        return await _missing("app.pipeline.act.run_act", payload)
    return await run_act(payload.get("cluster_id"))


async def llmo_probe(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    try:
        from app.pipeline.llmo import run_probe
    except ImportError:
        return await _missing("app.pipeline.llmo.run_probe", payload)
    return await run_probe(payload.get("brand_id"))


async def score_recompute(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    try:
        from app.pipeline.brand_scoring import recompute
    except ImportError:
        return await _missing("app.pipeline.brand_scoring.recompute", payload)
    return await recompute(payload.get("brand_id"))


async def draft_correction(ctx: dict[str, Any], payload: dict[str, Any]) -> Any:
    # TODO(Track 1): wire this to app.pipeline.act.run_correction after LLMO drift
    # detection lands in app.pipeline.llmo.
    try:
        from app.pipeline.act import run_correction
    except ImportError:
        return await _missing("app.pipeline.act.run_correction", payload)
    return await run_correction(payload.get("brand_id"), payload.get("audit_ids", []))


async def startup(ctx: dict[str, Any]) -> None:
    for dependency, function_name in (
        ("app.core.db", "init_pool"),
        ("app.core.ch", "init_clickhouse"),
    ):
        try:
            module = __import__(dependency, fromlist=[function_name])
            fn: Callable[[], Awaitable[Any]] = getattr(module, function_name)
        except (ImportError, AttributeError):
            continue
        await fn()


class WorkerSettings:
    functions = [
        monitor_persist,
        cluster_run,
        score_run,
        act_run,
        llmo_probe,
        score_recompute,
        draft_correction,
    ]
    redis_settings = _redis_settings()
    on_startup = startup
