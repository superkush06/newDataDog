"""Brand-level score API."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query

try:
    from app.core.db import pool
except ImportError:
    pool = None


router = APIRouter()


async def _recompute(brand_id: str) -> dict[str, Any] | None:
    try:
        from app.pipeline.brand_scoring import recompute
    except ImportError:
        return None
    return await recompute(brand_id)


@router.get("/scores")
async def scores(brand_id: str = Query(...), recompute_now: bool = False) -> dict[str, Any]:
    if recompute_now:
        recomputed = await _recompute(brand_id)
        if recomputed is not None:
            return recomputed

    if pool is None:
        return {
            "brand_id": brand_id,
            "overall": 0,
            "social": 0,
            "llmo": 0,
            "social_breakdown": {},
            "llmo_breakdown": {"per_provider": {}},
            "sparklines": {"overall": [], "social": [], "llmo": []},
            "mode": "placeholder",
            "reason": "missing_db",
        }

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT overall, social, llmo, breakdown, created_at
            FROM pulse_scores
            WHERE brand_id=$1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            uuid.UUID(brand_id),
        )
        spark_rows = await conn.fetch(
            """
            SELECT overall, social, llmo
            FROM pulse_scores
            WHERE brand_id=$1 AND created_at > now() - INTERVAL '24 hours'
            ORDER BY created_at ASC
            """,
            uuid.UUID(brand_id),
        )

    if row is None:
        recomputed = await _recompute(brand_id)
        if recomputed is not None:
            return recomputed
        return {
            "brand_id": brand_id,
            "overall": 0,
            "social": 0,
            "llmo": 0,
            "social_breakdown": {},
            "llmo_breakdown": {"per_provider": {}},
            "sparklines": {"overall": [], "social": [], "llmo": []},
        }

    breakdown = row["breakdown"] if isinstance(row["breakdown"], dict) else {}
    return {
        "brand_id": brand_id,
        "overall": row["overall"],
        "social": row["social"],
        "llmo": row["llmo"],
        **breakdown,
        "computed_at": row["created_at"].isoformat() if row["created_at"] else None,
        "sparklines": {
            "overall": [item["overall"] for item in spark_rows],
            "social": [item["social"] for item in spark_rows],
            "llmo": [item["llmo"] for item in spark_rows],
        },
    }
