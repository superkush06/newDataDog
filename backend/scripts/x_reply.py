"""Operator-triggered Pulse reply.

Usage:
  .venv/bin/python scripts/x_reply.py <tweet_url_or_id>
  .venv/bin/python scripts/x_reply.py <tweet_url_or_id> --force      # skip relevance gate
  .venv/bin/python scripts/x_reply.py <tweet_url_or_id> --dry-run    # don't post

Flow: oEmbed fetch → keyword + author gate → Groq relevance gate → Groq draft → X post.
Same logic as the autonomous monitor, just URL-triggered (X Free tier has no
read credits, so polling is paywalled).
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import urllib.parse
import webbrowser

from app.agents.x_agent.config import load_config


def requests_quote(s: str) -> str:
    return urllib.parse.quote(s, safe="")
from app.agents.x_agent.context import RelevanceAnalyzer
from app.agents.x_agent.monitor import Tweet
from app.agents.x_agent.oembed import extract_tweet_id, fetch_tweet
from app.agents.x_agent.poster import XPoster
from app.agents.x_agent.responder import GroqResponder
from app.agents.x_agent.store import TweetStore


def _log() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s | %(message)s",
        stream=sys.stdout,
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("url_or_id", help="tweet URL or raw numeric id")
    p.add_argument("--force", action="store_true",
                   help="skip the keyword + relevance gates")
    p.add_argument("--dry-run", action="store_true",
                   help="generate the draft but do not post")
    p.add_argument("--approve", action="store_true",
                   help="human-approval mode: draft + copy to clipboard + open X compose")
    args = p.parse_args()

    _log()
    log = logging.getLogger("x_reply")

    cfg = load_config()
    tweet_id = extract_tweet_id(args.url_or_id)
    if not tweet_id:
        log.error("could not extract tweet id from %r", args.url_or_id)
        return 2

    log.info("fetching tweet %s via syndication", tweet_id)
    fetched = fetch_tweet(tweet_id)
    if not fetched:
        log.error("tweet not retrievable (deleted, private, or wrong id)")
        return 3

    log.info("tweet by @%s: %s", fetched.author_handle, fetched.text)
    log.info("creds — x_write=%s groq=%s",
             cfg.has_x_write_creds, bool(cfg.groq_api_key))

    store = TweetStore(cfg.db_path)
    if store.is_processed(fetched.id) and not args.force:
        log.warning("already processed %s — pass --force to override", fetched.id)
        return 4

    tweet = Tweet(
        id=fetched.id,
        author_handle=fetched.author_handle,
        text=fetched.text,
        created_at=fetched.created_at,
        in_reply_to_id=fetched.in_reply_to_id,
        conversation_id=None,
        source="oembed",
    )

    # Author + keyword gate (skip with --force)
    if not args.force:
        if tweet.author_handle.lower() != cfg.target_handle.lower():
            log.error("author @%s != target @%s — refusing (pass --force to override)",
                      tweet.author_handle, cfg.target_handle)
            store.record(
                tweet_id=tweet.id, author_handle=tweet.author_handle,
                decision="skipped", reason="wrong_author", tweet_text=tweet.text,
            )
            return 5
        if cfg.keyword not in tweet.text.lower():
            log.error("keyword %r not in tweet — refusing (pass --force to override)",
                      cfg.keyword)
            store.record(
                tweet_id=tweet.id, author_handle=tweet.author_handle,
                decision="skipped", reason="keyword_absent", tweet_text=tweet.text,
            )
            return 6

    # Relevance gate (skip with --force)
    if not args.force:
        verdict = RelevanceAnalyzer(cfg).analyze(tweet, thread_context=None)
        log.info("relevance: relevant=%s conf=%.2f reason=%s",
                 verdict.relevant, verdict.confidence, verdict.reason)
        if not verdict.relevant:
            store.record(
                tweet_id=tweet.id, author_handle=tweet.author_handle,
                matched_keyword=cfg.keyword,
                decision="skipped", reason=f"not_relevant: {verdict.reason}",
                tweet_text=tweet.text,
            )
            return 7

    # Draft
    draft = GroqResponder(cfg).generate(tweet, thread_context=None)
    log.info("draft (%d chars): %s", len(draft), draft)

    # Post
    if args.dry_run:
        log.info("[dry-run] not posting")
        store.record(
            tweet_id=tweet.id, author_handle=tweet.author_handle,
            matched_keyword=cfg.keyword, decision="skipped",
            reason="cli_dry_run", reply_text=draft, tweet_text=tweet.text,
        )
        return 0

    # Human-approval mode: copy draft to clipboard + open X compose window.
    # Lets us demo the full pipeline without the X Free-tier write paywall.
    if args.approve:
        try:
            subprocess.run(["pbcopy"], input=draft.encode(), check=True)
            log.info("✓ draft copied to clipboard")
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            log.warning("clipboard copy failed (%s) — paste manually", exc)
        compose_url = (
            f"https://x.com/intent/tweet?in_reply_to={tweet.id}"
            f"&text={requests_quote(draft)}"
        )
        log.info("opening compose window in browser")
        webbrowser.open(compose_url)
        store.record(
            tweet_id=tweet.id, author_handle=tweet.author_handle,
            matched_keyword=cfg.keyword, decision="skipped",
            reason="awaiting_human_approval", reply_text=draft, tweet_text=tweet.text,
        )
        log.info("→ paste from clipboard if not pre-filled, click Reply")
        return 0

    result = XPoster(cfg).reply(in_reply_to_tweet_id=tweet.id, text=draft)
    store.record(
        tweet_id=tweet.id, author_handle=tweet.author_handle,
        matched_keyword=cfg.keyword,
        decision="replied" if result.posted else "skipped",
        reason=None if result.posted else (result.error or "post_failed"),
        reply_id=result.reply_id, reply_text=draft, tweet_text=tweet.text,
    )

    if result.posted:
        log.info("✓ posted reply %s — https://x.com/i/web/status/%s",
                 result.reply_id, result.reply_id)
        return 0
    log.error("✗ post failed: %s", result.error)
    return 8


if __name__ == "__main__":
    sys.exit(main())
