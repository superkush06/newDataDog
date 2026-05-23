"""Tweet monitor — Nimble primary, X API v2 (tweepy) fallback.

Returns a normalized list of `Tweet` dicts so downstream stages don't care
which source produced them.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import requests
import tweepy

from .config import XAgentConfig

log = logging.getLogger("x_agent.monitor")


@dataclass
class Tweet:
    id: str
    author_handle: str
    text: str
    created_at: str | None
    in_reply_to_id: str | None
    conversation_id: str | None
    source: str  # 'nimble' | 'x_api'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TweetMonitor:
    def __init__(self, cfg: XAgentConfig) -> None:
        self.cfg = cfg
        self._nimble_failures = 0
        self._x_user_id: str | None = None
        self._x_client = self._build_x_client()

    # ───────────────────── X API (tweepy) ─────────────────────

    def _build_x_client(self) -> tweepy.Client | None:
        if not self.cfg.has_x_read_creds:
            return None
        return tweepy.Client(
            bearer_token=self.cfg.x_bearer_token,
            consumer_key=self.cfg.x_api_key,
            consumer_secret=self.cfg.x_api_secret,
            access_token=self.cfg.x_access_token,
            access_token_secret=self.cfg.x_access_token_secret,
            wait_on_rate_limit=False,
        )

    def _resolve_x_user_id(self) -> str | None:
        if self._x_user_id or not self._x_client:
            return self._x_user_id
        try:
            resp = self._x_client.get_user(username=self.cfg.target_handle)
            if resp and resp.data:
                self._x_user_id = str(resp.data.id)
                log.info("resolved x user_id for @%s → %s", self.cfg.target_handle, self._x_user_id)
        except tweepy.TweepyException as exc:
            log.warning("failed to resolve x user_id: %s", exc)
        return self._x_user_id

    def _fetch_via_x_api(self, since_id: str | None = None) -> list[Tweet]:
        if not self._x_client:
            return []
        user_id = self._resolve_x_user_id()
        if not user_id:
            return []
        try:
            params = {
                "id": user_id,
                "max_results": 10,
                "tweet_fields": ["created_at", "conversation_id", "in_reply_to_user_id", "referenced_tweets"],
                "exclude": ["retweets"],
            }
            if since_id:
                params["since_id"] = since_id
            resp = self._x_client.get_users_tweets(**params)
        except tweepy.TooManyRequests:
            log.warning("x api rate limited")
            return []
        except tweepy.TweepyException as exc:
            log.warning("x api error: %s", exc)
            return []
        if not resp or not resp.data:
            return []
        out: list[Tweet] = []
        for t in resp.data:
            in_reply_to = None
            for ref in (t.referenced_tweets or []):
                if ref.type == "replied_to":
                    in_reply_to = str(ref.id)
                    break
            out.append(Tweet(
                id=str(t.id),
                author_handle=self.cfg.target_handle,
                text=t.text or "",
                created_at=t.created_at.isoformat() if t.created_at else None,
                in_reply_to_id=in_reply_to,
                conversation_id=str(t.conversation_id) if t.conversation_id else None,
                source="x_api",
            ))
        return out

    # ───────────────────── Nimble ─────────────────────────────

    def _fetch_via_nimble(self) -> list[Tweet]:
        if not self.cfg.has_nimble:
            return []
        query = f"from:{self.cfg.target_handle} {self.cfg.keyword}"
        try:
            r = requests.post(
                self.cfg.nimble_x_endpoint,
                headers={
                    "Authorization": f"Basic {self.cfg.nimble_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "search_engine": "twitter_search",
                    "country": "US",
                    "locale": "en",
                    "parse": True,
                },
                timeout=30,
            )
            if r.status_code >= 400:
                log.warning("nimble HTTP %s: %s", r.status_code, r.text[:200])
                self._nimble_failures += 1
                return []
            self._nimble_failures = 0
            return self._parse_nimble(r.json())
        except requests.RequestException as exc:
            log.warning("nimble request failed: %s", exc)
            self._nimble_failures += 1
            return []

    def _parse_nimble(self, payload: dict) -> list[Tweet]:
        items = (
            payload.get("parsing", {}).get("entities", {}).get("Tweet")
            or payload.get("items")
            or payload.get("results")
            or []
        )
        out: list[Tweet] = []
        for item in items:
            tid = str(item.get("id") or item.get("tweet_id") or item.get("url", ""))
            if not tid:
                continue
            handle = (
                item.get("author_handle") or item.get("username")
                or (item.get("user") or {}).get("screen_name") or ""
            ).lstrip("@")
            if handle.lower() != self.cfg.target_handle.lower():
                continue
            out.append(Tweet(
                id=tid,
                author_handle=handle,
                text=item.get("text") or item.get("content") or "",
                created_at=item.get("created_at") or item.get("posted_at"),
                in_reply_to_id=item.get("in_reply_to_status_id_str"),
                conversation_id=item.get("conversation_id"),
                source="nimble",
            ))
        return out

    # ───────────────────── Public ─────────────────────────────

    def fetch(self, since_id: str | None = None) -> list[Tweet]:
        if self.cfg.has_nimble and self._nimble_failures < 2:
            tweets = self._fetch_via_nimble()
            if tweets:
                return tweets
        return self._fetch_via_x_api(since_id=since_id)

    def fetch_thread_context(self, tweet: Tweet) -> str | None:
        if not tweet.in_reply_to_id or not self._x_client:
            return None
        try:
            resp = self._x_client.get_tweet(
                id=tweet.in_reply_to_id,
                tweet_fields=["author_id", "created_at"],
                expansions=["author_id"],
            )
        except tweepy.TweepyException as exc:
            log.warning("thread context fetch failed: %s", exc)
            return None
        if not resp or not resp.data:
            return None
        parent_handle = ""
        if resp.includes and resp.includes.get("users"):
            parent_handle = "@" + resp.includes["users"][0].username
        return f"{parent_handle}: {resp.data.text}".strip()
