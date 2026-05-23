"""X/Twitter payload normalizer."""
from __future__ import annotations

from typing import Any

from app.adapters.base import NormalizedPost, parse_datetime


class XAdapter:
    platform = "x"

    def normalize(self, payload: dict[str, Any]) -> list[NormalizedPost]:
        records = payload.get("data")
        if records is None:
            records = payload.get("tweets") or payload.get("posts") or []
        if isinstance(records, dict):
            records = [records]

        users = {
            str(user.get("id")): user
            for user in payload.get("includes", {}).get("users", [])
            if user.get("id") is not None
        }

        posts: list[NormalizedPost] = []
        for item in records:
            author = users.get(str(item.get("author_id")), {})
            external_id = str(item.get("id") or item.get("tweet_id") or "")
            handle = item.get("author_handle") or author.get("username")
            url = item.get("url")
            if not url and external_id:
                url = f"https://x.com/{handle or 'i'}/status/{external_id}"
            posts.append(
                NormalizedPost(
                    platform="x",
                    external_id=external_id,
                    brand_id=item.get("brand_id") or payload.get("brand_id"),
                    author_name=item.get("author_name") or author.get("name"),
                    author_handle=handle,
                    text=item.get("text") or "",
                    url=url,
                    created_at=parse_datetime(item.get("created_at")),
                    raw=item,
                )
            )
        return posts
