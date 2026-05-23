"""Meta webhook payload normalizer for Instagram and Facebook-like events."""
from __future__ import annotations

from typing import Any

from app.adapters.base import NormalizedPost, parse_datetime


class MetaAdapter:
    platform = "meta"

    def normalize(self, payload: dict[str, Any]) -> list[NormalizedPost]:
        if "entry" in payload:
            return self._from_webhook_entries(payload)

        record = payload.get("data") or payload
        platform = self._platform_for(payload, record)
        return [self._post_from_record(record, platform, payload.get("brand_id"))]

    def _from_webhook_entries(self, payload: dict[str, Any]) -> list[NormalizedPost]:
        posts: list[NormalizedPost] = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value") or {}
                platform = self._platform_for(payload, value)
                posts.append(self._post_from_record(value, platform, payload.get("brand_id")))
        return posts

    def _post_from_record(
        self, record: dict[str, Any], platform: str, brand_id: str | None
    ) -> NormalizedPost:
        external_id = str(
            record.get("id")
            or record.get("post_id")
            or record.get("comment_id")
            or record.get("media_id")
            or ""
        )
        return NormalizedPost(
            platform=platform,
            external_id=external_id,
            brand_id=record.get("brand_id") or brand_id,
            author_name=record.get("from", {}).get("name")
            if isinstance(record.get("from"), dict)
            else record.get("author_name"),
            author_handle=record.get("username") or record.get("author_handle"),
            text=record.get("text") or record.get("message") or record.get("caption") or "",
            url=record.get("permalink") or record.get("url"),
            created_at=parse_datetime(record.get("timestamp") or record.get("created_time")),
            raw=record,
        )

    def _platform_for(self, payload: dict[str, Any], record: dict[str, Any]) -> str:
        source = (
            record.get("platform")
            or payload.get("platform")
            or payload.get("object")
            or "facebook"
        )
        if source in {"instagram", "facebook"}:
            return source
        return "facebook"
