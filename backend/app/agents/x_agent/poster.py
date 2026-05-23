"""X API v2 reply poster. Uses tweepy with OAuth 1.0a user context (the only
auth path that lets you POST /2/tweets)."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import tweepy

from .config import XAgentConfig

log = logging.getLogger("x_agent.poster")


@dataclass
class PostResult:
    posted: bool
    reply_id: str | None
    error: str | None


class XPoster:
    def __init__(self, cfg: XAgentConfig) -> None:
        self.cfg = cfg
        self._client = self._build_client()

    def _build_client(self) -> tweepy.Client | None:
        if not self.cfg.has_x_write_creds:
            return None
        return tweepy.Client(
            consumer_key=self.cfg.x_api_key,
            consumer_secret=self.cfg.x_api_secret,
            access_token=self.cfg.x_access_token,
            access_token_secret=self.cfg.x_access_token_secret,
            wait_on_rate_limit=False,
        )

    def reply(self, *, in_reply_to_tweet_id: str, text: str) -> PostResult:
        if self.cfg.dry_run:
            log.info("[dry-run] would reply to %s: %s", in_reply_to_tweet_id, text)
            return PostResult(posted=False, reply_id=None, error="dry_run")
        if not self._client:
            return PostResult(posted=False, reply_id=None, error="missing_x_write_creds")

        attempts = 0
        last_err: str | None = None
        while attempts < 3:
            attempts += 1
            try:
                resp = self._client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=in_reply_to_tweet_id,
                )
                reply_id = str(resp.data["id"]) if resp and resp.data else None
                log.info("posted reply %s -> parent %s", reply_id, in_reply_to_tweet_id)
                return PostResult(posted=True, reply_id=reply_id, error=None)
            except tweepy.TooManyRequests as exc:
                last_err = f"rate_limited: {exc}"
                # Tweepy attaches reset epoch via response headers when available
                wait = 30 * attempts
                log.warning("rate limited, backing off %ss (attempt %s/3)", wait, attempts)
                time.sleep(wait)
            except tweepy.Forbidden as exc:
                # 403 is non-retryable — usually duplicate, blocked, or
                # missing OAuth 1.0a scope. Stop immediately.
                last_err = f"forbidden: {exc}"
                log.error("%s", last_err)
                break
            except tweepy.TweepyException as exc:
                last_err = f"tweepy_error: {exc}"
                log.warning("post failed (attempt %s/3): %s", attempts, exc)
                time.sleep(5 * attempts)
        return PostResult(posted=False, reply_id=None, error=last_err or "unknown")
