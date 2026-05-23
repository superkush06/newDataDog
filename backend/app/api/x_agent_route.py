"""HTTP entry point for the URL-triggered X reply agent.

Mirrors `scripts/x_reply.py` but exposed via REST so the dashboard can run it
with a button. Returns the full pipeline trace so the UI can render each stage
(fetch → gate → relevance → draft) as the agent works through them.
"""
from __future__ import annotations

import urllib.parse
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.x_agent.config import load_config
from app.agents.x_agent.context import RelevanceAnalyzer
from app.agents.x_agent.monitor import Tweet
from app.agents.x_agent.oembed import extract_tweet_id, fetch_tweet
from app.agents.x_agent.responder import GroqResponder
from app.agents.x_agent.store import TweetStore

router = APIRouter(prefix="/x_agent")


class ReplyRequest(BaseModel):
    tweet_url: str = Field(..., description="Tweet URL or numeric id")
    force: bool = Field(default=False, description="Skip author + keyword + relevance gates")


class ReplyResponse(BaseModel):
    tweet: dict[str, Any]
    gates: dict[str, Any]
    draft: str | None = None
    compose_url: str | None = None
    already_processed: bool = False


@router.post("/reply", response_model=ReplyResponse)
def reply(req: ReplyRequest) -> ReplyResponse:
    cfg = load_config()

    tweet_id = extract_tweet_id(req.tweet_url)
    if not tweet_id:
        raise HTTPException(400, "could not extract tweet id from input")

    fetched = fetch_tweet(tweet_id)
    if not fetched:
        raise HTTPException(404, "tweet not retrievable (deleted, private, or wrong id)")

    tweet_payload = {
        "id": fetched.id,
        "author_handle": fetched.author_handle,
        "text": fetched.text,
        "created_at": fetched.created_at,
    }

    store = TweetStore(cfg.db_path)
    already_processed = store.is_processed(fetched.id) and not req.force

    tweet = Tweet(
        id=fetched.id, author_handle=fetched.author_handle, text=fetched.text,
        created_at=fetched.created_at, in_reply_to_id=fetched.in_reply_to_id,
        conversation_id=None, source="oembed",
    )

    gates: dict[str, Any] = {
        "author_ok": tweet.author_handle.lower() == cfg.target_handle.lower(),
        "keyword_ok": cfg.keyword in tweet.text.lower(),
        "relevance": None,
    }

    if not req.force:
        if not gates["author_ok"]:
            store.record(tweet_id=tweet.id, author_handle=tweet.author_handle,
                         decision="skipped", reason="wrong_author", tweet_text=tweet.text)
            return ReplyResponse(tweet=tweet_payload, gates=gates,
                                 already_processed=already_processed)
        if not gates["keyword_ok"]:
            store.record(tweet_id=tweet.id, author_handle=tweet.author_handle,
                         decision="skipped", reason="keyword_absent", tweet_text=tweet.text)
            return ReplyResponse(tweet=tweet_payload, gates=gates,
                                 already_processed=already_processed)

        verdict = RelevanceAnalyzer(cfg).analyze(tweet, thread_context=None)
        gates["relevance"] = {
            "relevant": verdict.relevant,
            "confidence": round(verdict.confidence, 2),
            "reason": verdict.reason,
        }
        if not verdict.relevant:
            store.record(tweet_id=tweet.id, author_handle=tweet.author_handle,
                         matched_keyword=cfg.keyword, decision="skipped",
                         reason=f"not_relevant: {verdict.reason}", tweet_text=tweet.text)
            return ReplyResponse(tweet=tweet_payload, gates=gates,
                                 already_processed=already_processed)

    draft = GroqResponder(cfg).generate(tweet, thread_context=None)
    compose_url = (
        "https://x.com/intent/tweet"
        f"?in_reply_to={tweet.id}"
        f"&text={urllib.parse.quote(draft, safe='')}"
    )

    store.record(
        tweet_id=tweet.id, author_handle=tweet.author_handle,
        matched_keyword=cfg.keyword, decision="skipped",
        reason="awaiting_human_approval",
        reply_text=draft, tweet_text=tweet.text,
    )

    return ReplyResponse(
        tweet=tweet_payload, gates=gates, draft=draft,
        compose_url=compose_url, already_processed=already_processed,
    )
