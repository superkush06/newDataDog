"""LLMO audit and prompt APIs."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

try:
    from app.core.ch import ch
except ImportError:
    ch = None

try:
    from app.core.db import pool
except ImportError:
    pool = None

try:
    from app.core.queue import enqueue as _track1_enqueue
except ImportError:
    _track1_enqueue = None


router = APIRouter()


class PromptBody(BaseModel):
    prompt: str
    intent: str = "discovery"


async def enqueue_probe(brand_id: str) -> dict[str, Any]:
    if _track1_enqueue is None:
        return {"status": "skipped", "reason": "missing_queue", "brand_id": brand_id}
    await _track1_enqueue("llmo_probe", {"brand_id": brand_id})
    return {"status": "enqueued", "brand_id": brand_id}


@router.get("/llmo/audits")
async def audits(
    brand_id: str = Query(...),
    provider: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    if ch is None:
        return {"audits": [], "mode": "placeholder", "reason": "missing_clickhouse"}

    where = ["brand_id = %(brand_id)s"]
    params: dict[str, Any] = {"brand_id": brand_id, "limit": limit}
    if provider:
        where.append("provider = %(provider)s")
        params["provider"] = provider
    rows = (
        await ch().query(
            f"""
            SELECT id, prompt_id, provider, model, prompt, response, cited,
                   mention_rank, visibility_score, sentiment_score, citations,
                   claims, drift_score, created_at
            FROM llmo_audits
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC
            LIMIT %(limit)s
            """,
            params,
        )
    ).result_rows
    return {
        "audits": [
            {
                "id": str(row[0]),
                "prompt_id": str(row[1]) if row[1] else None,
                "provider": row[2],
                "model": row[3],
                "prompt": row[4],
                "response": row[5],
                "cited": bool(row[6]),
                "mention_rank": row[7],
                "visibility_score": row[8],
                "sentiment_score": row[9],
                "citations": list(row[10] or []),
                "claims": list(row[11] or []),
                "drift_score": row[12],
                "created_at": row[13].isoformat() if row[13] else None,
            }
            for row in rows
        ]
    }


@router.post("/llmo/probe")
async def probe(brand_id: str = Query(...)) -> dict[str, Any]:
    return await enqueue_probe(brand_id)


@router.get("/brands/{brand_id}/prompts")
async def list_prompts(brand_id: str) -> dict[str, Any]:
    if pool is None:
        return {"prompts": [], "mode": "placeholder", "reason": "missing_db"}
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, prompt, intent, created_at
            FROM brand_prompts
            WHERE brand_id=$1
            ORDER BY created_at DESC
            """,
            uuid.UUID(brand_id),
        )
    return {
        "prompts": [
            {
                "id": str(row["id"]),
                "prompt": row["prompt"],
                "intent": row["intent"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in rows
        ]
    }


@router.post("/brands/{brand_id}/prompts")
async def add_prompt(brand_id: str, body: PromptBody) -> dict[str, Any]:
    if pool is None:
        return {
            "id": None,
            "brand_id": brand_id,
            "prompt": body.prompt,
            "intent": body.intent,
            "mode": "placeholder",
            "reason": "missing_db",
        }
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO brand_prompts (brand_id, prompt, intent)
            VALUES ($1,$2,$3)
            RETURNING id
            """,
            uuid.UUID(brand_id),
            body.prompt,
            body.intent,
        )
    return {"id": str(row["id"]), "brand_id": brand_id}
