"""Nimble structured mention payload normalizer."""
from __future__ import annotations

from typing import Any

from app.adapters.base import NormalizedPost, parse_datetime


class NimbleAdapter:
    platform = "nimble"

    def normalize(self, payload: dict[str, Any]) -> list[NormalizedPost]:
        items = payload.get("items") or payload.get("results") or []
        return [self._from_item(item, payload.get("brand_id")) for item in items]

    def _from_item(self, item: dict[str, Any], brand_id: str | None) -> NormalizedPost:
        return NormalizedPost(
            platform=str(item.get("platform") or item.get("source") or "web"),
            external_id=str(item.get("id") or item.get("url") or ""),
            brand_id=item.get("brand_id") or brand_id,
            author_name=item.get("author_name") or item.get("author"),
            author_handle=item.get("author_handle") or item.get("username"),
            text=item.get("text") or item.get("title") or item.get("content") or "",
            url=item.get("url") or item.get("permalink"),
            created_at=parse_datetime(item.get("created_at") or item.get("posted_at")),
            raw=item,
        )
