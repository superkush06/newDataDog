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
        where.append("llm = %(provider)s")
        params["provider"] = provider
    rows = (
        await ch().query(
            f"""
            SELECT id, brand_id, llm, prompt, prompt_id, response, mentioned,
                   position, competitors_mentioned, sentiment, claims,
                   drift_score, citation_accuracy, ingested_at
            FROM llmo_audits
            WHERE {' AND '.join(where)}
            ORDER BY ingested_at DESC
            LIMIT %(limit)s
            """,
            params,
        )
    ).result_rows
    return {
        "audits": [
            {
                "id": str(row[0]),
                "brand_id": str(row[1]),
                "llm": row[2],
                "prompt": row[3],
                "prompt_id": str(row[4]) if row[4] else None,
                "response": row[5],
                "mentioned": bool(row[6]),
                "position": int(row[7]),
                "competitors_mentioned": list(row[8] or []),
                "sentiment": float(row[9]),
                "claims": list(row[10] or []),
                "drift_score": float(row[11]),
                "citation_accuracy": float(row[12]),
                "ingested_at": row[13].isoformat() if row[13] else None,
            }
            for row in rows
        ]
    }


@router.post("/llmo/probe")
async def probe(brand_id: str = Query(...)) -> dict[str, Any]:
    return await enqueue_probe(brand_id)


@router.get("/brands/{brand_id}/prompts")
async def list_prompts(brand_id: str) -> dict[str, Any]:
    if not pool:
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
    if not pool:
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
