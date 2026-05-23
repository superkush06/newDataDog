"""Webhook ingestion routes."""
from __future__ import annotations

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.adapters import get_adapter

try:
    from app.config import settings
except ImportError:
    settings = None

try:
    from app.core.queue import enqueue as _track1_enqueue
except ImportError:
    _track1_enqueue = None


router = APIRouter()


def _setting(name: str) -> str:
    if settings is None:
        return ""
    return str(getattr(settings, name, "") or "")


def secret_for_platform(platform: str) -> str:
    platform = platform.lower()
    if platform in {"x", "twitter"}:
        return _setting("x_webhook_secret")
    if platform in {"meta", "instagram", "facebook"}:
        return _setting("meta_app_secret")
    if platform == "nimble":
        return _setting("nimble_webhook_secret") or _setting("nimble_api_key")
    return ""


def verify_hmac(raw_body: bytes, signature: str | None, secret: str) -> bool:
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


async def enqueue_monitor_job(payload: dict[str, Any]) -> dict[str, Any]:
    if _track1_enqueue is None:
        return {"status": "skipped", "reason": "missing_queue"}
    await _track1_enqueue("monitor_persist", payload)
    return {"status": "enqueued"}


@router.post("/{platform}")
async def ingest_webhook(
    platform: str,
    request: Request,
    brand_id: str | None = Query(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, Any]:
    raw_body = await request.body()
    if not verify_hmac(raw_body, x_hub_signature_256, secret_for_platform(platform)):
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        adapter = get_adapter(platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = await request.json()
    posts = adapter.normalize(payload)
    queue_results = []
    for post in posts:
        if brand_id and post.brand_id is None:
            post.brand_id = brand_id
        queue_results.append(
            await enqueue_monitor_job(
                {
                    "brand_id": post.brand_id or brand_id,
                    "post": post.model_dump(mode="json"),
                }
            )
        )

    return {
        "status": "accepted",
        "platform": platform,
        "normalized": len(posts),
        "queue": queue_results,
    }
