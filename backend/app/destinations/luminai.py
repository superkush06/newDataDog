"""Luminai destination client for health-system workflow actions."""
from __future__ import annotations

from typing import Any

import httpx

try:
    from app.config import settings
except ImportError:
    settings = None


DEFAULT_BASE_URL = "https://api.luminai.com/v1"


def _api_key(api_key: str | None = None) -> str:
    if api_key is not None:
        return api_key
    if settings is None:
        return ""
    return settings.luminai_api_key


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


async def execute_workflow(
    workflow_id: str | None,
    payload: dict[str, Any],
    *,
    api_key: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 15.0,
) -> dict[str, Any]:
    key = _api_key(api_key)
    if not key:
        return {"ok": False, "status": "skipped", "reason": "missing_luminai_api_key"}
    if not workflow_id:
        return {"ok": False, "status": "skipped", "reason": "missing_workflow_id"}

    url = f"{base_url.rstrip('/')}/workflows/{workflow_id}/instances"
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=_headers(key), json=payload)

    try:
        body: Any = response.json()
    except ValueError:
        body = response.text

    return {
        "ok": 200 <= response.status_code < 300,
        "status": response.status_code,
        "body": body,
    }


async def classify_workflow(
    summary: str,
    *,
    api_key: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 15.0,
) -> dict[str, Any]:
    key = _api_key(api_key)
    if not key:
        return {"ok": False, "status": "skipped", "reason": "missing_luminai_api_key"}

    url = f"{base_url.rstrip('/')}/workflows/classify"
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=_headers(key), json={"summary": summary})

    try:
        body: Any = response.json()
    except ValueError:
        body = response.text

    return {
        "ok": 200 <= response.status_code < 300,
        "status": response.status_code,
        "body": body,
    }
