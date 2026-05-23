"""Core REST API routes."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import Brand, DecisionBody

try:
    from app.core.db import pool
except ImportError:
    pool = None

try:
    from app.core.ch import ch
except ImportError:
    ch = None


router = APIRouter()


class PlaceholderStore:
    reason = "track1_dependency_missing"

    @staticmethod
    def meta() -> dict[str, str]:
        return {"mode": "placeholder", "reason": PlaceholderStore.reason}


class BrandPatch(BaseModel):
    name: str | None = None
    vertical: str | None = None
    voice_guidelines: str | None = None
    keywords: list[str] | None = None
    thresholds: dict[str, Any] | None = None
    connections: dict[str, Any] | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _postgres_ok() -> str:
    if not pool:
        return "missing"
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return "connected"
    except Exception as exc:
        return f"error: {exc}"


async def _clickhouse_ok() -> str:
    if ch is None:
        return "missing"
    try:
        await ch().query("SELECT 1")
        return "connected"
    except Exception as exc:
        return f"error: {exc}"


@router.get("/health")
async def health() -> dict[str, Any]:
    services = {
        "postgres": await _postgres_ok(),
        "clickhouse": await _clickhouse_ok(),
    }
    has_error = any(value.startswith("error:") for value in services.values())
    return {
        "status": "degraded" if has_error else "ok",
        "services": services,
        "timestamp": _now(),
    }


@router.get("/feed")
async def feed(
    brand_id: str = Query(...),
    platform: str | None = None,
    sentiment: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    if ch is None:
        return {
            "posts": [],
            "next_cursor": None,
            "stats": {
                "volume_24h": 0,
                "sentiment_7d": [],
                "platform_distribution": {},
                "avg_response_minutes": 0,
            },
            **PlaceholderStore.meta(),
        }

    where = ["brand_id = %(brand_id)s"]
    params: dict[str, Any] = {"brand_id": brand_id, "limit": limit}
    if platform:
        where.append("platform = %(platform)s")
        params["platform"] = platform
    if sentiment:
        where.append("sentiment = %(sentiment)s")
        params["sentiment"] = sentiment

    rows = (
        await ch().query(
            f"""
            SELECT id, platform, platform_post_id, author_handle,
                   author_follower_count, text, media_urls, likes, shares, comments,
                   permalink, posted_at, ingested_at, sentiment, cluster_id
            FROM posts FINAL
            WHERE {' AND '.join(where)}
            ORDER BY ingested_at DESC
            LIMIT %(limit)s
            """,
            params,
        )
    ).result_rows
    return {
        "posts": [
            {
                "id": str(row[0]),
                "platform": row[1],
                "platform_post_id": row[2],
                "author_handle": row[3],
                "author_follower_count": int(row[4] or 0),
                "text": row[5],
                "media_urls": list(row[6] or []),
                "likes": int(row[7] or 0),
                "shares": int(row[8] or 0),
                "comments": int(row[9] or 0),
                "permalink": row[10],
                "posted_at": row[11].isoformat() if row[11] else None,
                "ingested_at": row[12].isoformat() if row[12] else None,
                "sentiment": row[13],
                "cluster_id": str(row[14]) if row[14] else None,
            }
            for row in rows
        ],
        "next_cursor": None,
        "stats": {
            "volume_24h": len(rows),
            "sentiment_7d": [],
            "platform_distribution": {},
            "avg_response_minutes": 0,
        },
    }


@router.get("/clusters")
async def clusters(
    brand_id: str = Query(...),
    status: str = "active",
    min_severity: str | None = None,
) -> dict[str, Any]:
    if not pool:
        return {"clusters": [], "total": 0, **PlaceholderStore.meta()}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, summary, post_count, severity, severity_score, tags,
                   sentiment_breakdown, platforms, first_seen_at, last_activity_at, status
            FROM clusters
            WHERE brand_id=$1 AND status=$2
            ORDER BY severity_score DESC
            LIMIT 100
            """,
            uuid.UUID(brand_id),
            status,
        )
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    min_rank = severity_order.get(min_severity or "low", 0)
    items = [
        {
            "id": str(row["id"]),
            "name": row["name"],
            "summary": row["summary"],
            "post_count": row["post_count"],
            "severity": row["severity"],
            "severity_score": row["severity_score"],
            "tags": row["tags"],
            "sentiment_breakdown": row["sentiment_breakdown"],
            "platforms": row["platforms"],
            "first_seen_at": row["first_seen_at"].isoformat() if row["first_seen_at"] else None,
            "last_activity_at": row["last_activity_at"].isoformat()
            if row["last_activity_at"]
            else None,
            "status": row["status"],
        }
        for row in rows
        if severity_order.get(row["severity"], 0) >= min_rank
    ]
    return {"clusters": items, "total": len(items)}


@router.get("/queue")
async def queue(brand_id: str = Query(...), limit: int = Query(default=50, ge=1, le=200)):
    # TODO(Track 1): enrich with score breakdowns once scoring helpers and stores exist.
    if not pool:
        return {
            "queue": [],
            "threshold_config": {"critical": 700, "high": 400, "medium": 200},
            "weights": {},
            **PlaceholderStore.meta(),
        }
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, name, severity, severity_score
            FROM clusters
            WHERE brand_id=$1 AND status='active'
            ORDER BY severity_score DESC
            LIMIT $2
            """,
            uuid.UUID(brand_id),
            limit,
        )
    return {
        "queue": [
            {
                "cluster_id": str(row["id"]),
                "name": row["name"],
                "severity": row["severity"],
                "severity_score": row["severity_score"],
                "breakdown": {},
                "auto_escalate": row["severity"] == "critical",
            }
            for row in rows
        ],
        "threshold_config": {"critical": 700, "high": 400, "medium": 200},
        "weights": {},
    }


@router.get("/actions")
async def actions(
    brand_id: str = Query(...),
    type: str | None = None,
    state: str = "pending",
) -> dict[str, Any]:
    if not pool:
        return {"actions": [], "total": 0, **PlaceholderStore.meta()}
    where = "brand_id=$1 AND state=$2"
    params: list[Any] = [uuid.UUID(brand_id), state]
    if type:
        where += " AND type=$3"
        params.append(type)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT id, type, state, cluster_id, target_post_id, draft, context, created_at
            FROM actions
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT 100
            """,
            *params,
        )
    return {
        "actions": [
            {
                "id": str(row["id"]),
                "type": row["type"],
                "state": row["state"],
                "cluster_id": str(row["cluster_id"]),
                "target_post_id": str(row["target_post_id"]) if row["target_post_id"] else None,
                "draft": row["draft"],
                "context": row["context"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.post("/actions/{action_id}")
async def decide_action(action_id: str, body: DecisionBody) -> dict[str, Any]:
    if not pool:
        return {
            "id": action_id,
            "state": "skipped",
            "decision": body.decision,
            **PlaceholderStore.meta(),
        }
    new_state = "rejected" if body.decision == "reject" else "approved"
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE actions
            SET state=$1, decided_at=now(), reject_reason=$2
            WHERE id=$3 AND state='pending'
            """,
            new_state,
            body.reject_reason,
            action_id,
        )
    if result.endswith("0"):
        raise HTTPException(status_code=404, detail="pending action not found")
    return {"id": action_id, "state": new_state}


@router.post("/brands")
async def create_brand(brand: Brand) -> dict[str, Any]:
    if not pool:
        data = brand.model_dump()
        data.update(PlaceholderStore.meta())
        return data
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO brands (name, vertical, voice_guidelines, keywords, thresholds, connections)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb)
            RETURNING id, name
            """,
            brand.name,
            brand.vertical,
            brand.voice_guidelines,
            brand.keywords,
            json.dumps(brand.thresholds),
            json.dumps(brand.connections),
        )
    return {"id": str(row["id"]), "name": row["name"]}


@router.patch("/brands/{brand_id}")
async def update_brand(brand_id: str, patch: BrandPatch) -> dict[str, Any]:
    # TODO(Track 1): implement DB-backed partial update during integration.
    if not pool:
        return {"id": brand_id, "updated": patch.model_dump(exclude_none=True), **PlaceholderStore.meta()}
    raise HTTPException(status_code=501, detail="brand patch integration pending")
