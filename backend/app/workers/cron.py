"""Cron entrypoints for polling and maintenance jobs."""
from __future__ import annotations

import asyncio
from typing import Any

try:
    from app.core.queue import enqueue as _track1_enqueue
except ImportError:
    _track1_enqueue = None


async def enqueue_job(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    if _track1_enqueue is None:
        return {
            "status": "skipped",
            "reason": "missing_queue",
            "job": name,
            "payload": payload,
        }
    await _track1_enqueue(name, payload)
    return {"status": "enqueued", "job": name}


async def poll_platforms() -> dict[str, Any]:
    # TODO(Track 1): read brands from Postgres and poll Nimble per brand.
    return {
        "status": "skipped",
        "reason": "track1_brand_store_missing",
        "job": "poll_platforms",
    }


async def refresh_engagement() -> dict[str, Any]:
    # TODO(Track 1): re-fetch platform engagement and enqueue score recomputes.
    return {
        "status": "skipped",
        "reason": "track1_engagement_refresh_missing",
        "job": "refresh_engagement",
    }


async def run_llmo_probes() -> dict[str, Any]:
    # TODO(Track 1): load brand ids from Postgres when the DB helper lands.
    return {
        "status": "skipped",
        "reason": "track1_brand_store_missing",
        "job": "run_llmo_probes",
    }


COMMANDS = {
    "poll_platforms": poll_platforms,
    "refresh_engagement": refresh_engagement,
    "run_llmo_probes": run_llmo_probes,
}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        available = ", ".join(sorted(COMMANDS))
        raise SystemExit(f"usage: python -m app.workers.cron <{available}>")
    print(asyncio.run(COMMANDS[sys.argv[1]]()))
