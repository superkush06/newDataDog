"""Slack destination client."""
from __future__ import annotations

from typing import Any

import httpx


async def post_message(
    webhook_url: str | None,
    text: str,
    blocks: list[dict[str, Any]] | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    if not webhook_url:
        return {"ok": False, "status": "skipped", "reason": "missing_webhook_url"}

    payload: dict[str, Any] = {"text": text}
    if blocks is not None:
        payload["blocks"] = blocks

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(webhook_url, json=payload)

    return {
        "ok": 200 <= response.status_code < 300,
        "status": response.status_code,
        "reason": None if 200 <= response.status_code < 300 else response.text,
    }
