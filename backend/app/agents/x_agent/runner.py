"""Main loop — composes monitor → context → responder → poster with the
SQLite dedup store as the source of truth for 'have I handled this tweet'."""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Any

from .config import XAgentConfig, load_config
from .context import RelevanceAnalyzer
from .monitor import TweetMonitor
from .poster import XPoster
from .responder import GroqResponder
from .store import TweetStore

log = logging.getLogger("x_agent")


def _setup_logging() -> None:
    fmt = "%(asctime)s %(levelname)-5s %(name)s | %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt, stream=sys.stdout)


class XAgent:
    def __init__(self, cfg: XAgentConfig | None = None) -> None:
        self.cfg = cfg or load_config()
        self.store = TweetStore(self.cfg.db_path)
        self.monitor = TweetMonitor(self.cfg)
        self.analyzer = RelevanceAnalyzer(self.cfg)
        self.responder = GroqResponder(self.cfg)
        self.poster = XPoster(self.cfg)
        self._last_seen_id: str | None = self._highest_processed_id()
        self._stop = asyncio.Event()

    def _highest_processed_id(self) -> str | None:
        rows = self.store.recent(limit=200)
        if not rows:
            return None
        # Tweet IDs are monotonic; return the max as a since_id for X API
        try:
            return str(max(int(r["tweet_id"]) for r in rows if r["tweet_id"].isdigit()))
        except ValueError:
            return None

    def _process_tweet(self, tweet: Any) -> None:
        if self.store.is_processed(tweet.id):
            return

        text_lc = tweet.text.lower()
        if self.cfg.keyword not in text_lc:
            self.store.record(
                tweet_id=tweet.id, author_handle=tweet.author_handle,
                decision="skipped", reason="keyword_absent", tweet_text=tweet.text,
            )
            log.info("skip %s — keyword absent", tweet.id)
            return

        if tweet.author_handle.lower() != self.cfg.target_handle.lower():
            self.store.record(
                tweet_id=tweet.id, author_handle=tweet.author_handle,
                decision="skipped", reason="wrong_author", tweet_text=tweet.text,
            )
            log.info("skip %s — author %s != target", tweet.id, tweet.author_handle)
            return

        thread_ctx = self.monitor.fetch_thread_context(tweet)
        verdict = self.analyzer.analyze(tweet, thread_ctx)
        log.info("match %s — relevant=%s conf=%.2f reason=%s",
                 tweet.id, verdict.relevant, verdict.confidence, verdict.reason)

        if not verdict.relevant:
            self.store.record(
                tweet_id=tweet.id, author_handle=tweet.author_handle,
                matched_keyword=self.cfg.keyword,
                decision="skipped",
                reason=f"not_relevant: {verdict.reason}",
                tweet_text=tweet.text,
            )
            return

        reply_text = self.responder.generate(tweet, thread_ctx)
        log.info("draft for %s: %s", tweet.id, reply_text)

        result = self.poster.reply(in_reply_to_tweet_id=tweet.id, text=reply_text)
        decision = "replied" if result.posted else "skipped"
        reason = None if result.posted else (result.error or "post_failed")
        self.store.record(
            tweet_id=tweet.id,
            author_handle=tweet.author_handle,
            matched_keyword=self.cfg.keyword,
            decision=decision,
            reason=reason,
            reply_id=result.reply_id,
            reply_text=reply_text,
            tweet_text=tweet.text,
        )

    async def _tick(self) -> None:
        try:
            tweets = self.monitor.fetch(since_id=self._last_seen_id)
        except Exception as exc:  # noqa: BLE001
            log.exception("monitor fetch failed: %s", exc)
            return

        if not tweets:
            log.debug("no new tweets")
            return

        log.info("polled %s tweets (source=%s)", len(tweets), tweets[0].source if tweets else "-")
        for tweet in tweets:
            try:
                self._process_tweet(tweet)
                if tweet.id.isdigit():
                    if not self._last_seen_id or int(tweet.id) > int(self._last_seen_id):
                        self._last_seen_id = tweet.id
            except Exception as exc:  # noqa: BLE001
                log.exception("error handling tweet %s: %s", tweet.id, exc)

    async def run(self) -> None:
        _setup_logging()
        log.info(
            "x_agent starting — target=@%s keyword=%r poll=%ss dry_run=%s",
            self.cfg.target_handle, self.cfg.keyword,
            self.cfg.poll_interval_seconds, self.cfg.dry_run,
        )
        log.info(
            "creds — nimble=%s x_read=%s x_write=%s groq=%s",
            self.cfg.has_nimble, self.cfg.has_x_read_creds,
            self.cfg.has_x_write_creds, bool(self.cfg.groq_api_key),
        )

        while not self._stop.is_set():
            await self._tick()
            try:
                await asyncio.wait_for(
                    self._stop.wait(),
                    timeout=self.cfg.poll_interval_seconds,
                )
            except asyncio.TimeoutError:
                pass
        log.info("x_agent stopped")

    def stop(self) -> None:
        self._stop.set()


def main() -> None:
    agent = XAgent()
    loop = asyncio.new_event_loop()

    def _shutdown(*_: Any) -> None:
        log.info("shutdown signal received")
        agent.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            pass  # Windows

    try:
        loop.run_until_complete(agent.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
