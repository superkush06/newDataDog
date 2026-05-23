"""Adapter primitives for turning source payloads into normalized posts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field


class NormalizedPost(BaseModel):
    platform: str
    external_id: str
    text: str
    raw: dict[str, Any] = Field(default_factory=dict)
    brand_id: str | None = None
    author_name: str | None = None
    author_handle: str | None = None
    url: str | None = None
    created_at: datetime | None = None


class Adapter(Protocol):
    platform: str

    def normalize(self, payload: dict[str, Any]) -> list[NormalizedPost]:
        ...


_REGISTRY: dict[str, Adapter] = {}


def register(adapter: Adapter, *aliases: str) -> Adapter:
    keys = (adapter.platform, *aliases)
    for key in keys:
        _REGISTRY[key.lower()] = adapter
    return adapter


def get_adapter(platform: str) -> Adapter:
    try:
        return _REGISTRY[platform.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown adapter platform: {platform}") from exc


def registered_platforms() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
