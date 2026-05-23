"""Contextual relevance gate — decides whether the matched tweet is genuinely
about Crosby (and replying is appropriate) vs. sarcasm / a quote / unrelated
mention of 'crosby' (the name).

Uses Groq for a structured judgment so we don't post replies on jokes, hockey
chatter (Sidney Crosby), or quoted screenshots."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from groq import Groq

from .config import XAgentConfig
from .monitor import Tweet

log = logging.getLogger("x_agent.context")


@dataclass
class RelevanceVerdict:
    relevant: bool
    reason: str
    confidence: float


_SYSTEM = """You are a strict relevance classifier for an enterprise X auto-responder.
The brand is "Crosby" — an AI-first law firm (crosby.ai).

You will be given a tweet and (optionally) the parent tweet it is replying to.
Return JSON: {"relevant": bool, "reason": str, "confidence": 0.0-1.0}

Mark NOT relevant when:
- "crosby" refers to a person (Sidney Crosby the hockey player, Bing Crosby, David Crosby, anyone else named Crosby)
- the tweet is sarcastic, ironic, or mocking the brand without a real issue
- the tweet is quoting/screenshotting someone else's complaint
- the tweet is a meme, joke, or off-topic
- the tweet mentions Crosby but is not about Crosby's product, service, or company
- the tweet is a positive shoutout that doesn't need a reply

Mark relevant ONLY when the author is genuinely raising an issue, question,
feedback, or matter about Crosby (the company/product) that an official
response would naturally fit.

Be conservative — false positives are worse than false negatives."""


_QUICK_NEGATIVE_PATTERNS = [
    re.compile(r"\bsidney\s+crosby\b", re.I),
    re.compile(r"\bbing\s+crosby\b", re.I),
    re.compile(r"\bdavid\s+crosby\b", re.I),
    re.compile(r"\bcrosby\s+(stills|nash)\b", re.I),
    re.compile(r"\bpenguins?\b", re.I),  # Pittsburgh Penguins context
    re.compile(r"\bnhl\b", re.I),
]


class RelevanceAnalyzer:
    def __init__(self, cfg: XAgentConfig) -> None:
        self.cfg = cfg
        self._client = Groq(api_key=cfg.groq_api_key) if cfg.groq_api_key else None

    def _quick_reject(self, text: str) -> str | None:
        for pat in _QUICK_NEGATIVE_PATTERNS:
            if pat.search(text):
                return f"quick-reject: matched {pat.pattern!r}"
        return None

    def analyze(self, tweet: Tweet, thread_context: str | None) -> RelevanceVerdict:
        # Fast path: obvious "wrong Crosby" mentions
        reason = self._quick_reject(tweet.text)
        if reason:
            return RelevanceVerdict(relevant=False, reason=reason, confidence=0.95)

        if not self._client:
            # Without Groq we can't safely judge tone — fall back to allow,
            # but flag low confidence so the responder still posts cautiously.
            return RelevanceVerdict(relevant=True, reason="no-llm-judge", confidence=0.4)

        user_msg = f"Tweet: {tweet.text}\n"
        if thread_context:
            user_msg += f"In reply to: {thread_context}\n"

        try:
            resp = self._client.chat.completions.create(
                model=self.cfg.groq_model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=200,
            )
        except Exception as exc:  # noqa: BLE001 — log and fail safe
            log.warning("groq relevance call failed: %s", exc)
            return RelevanceVerdict(relevant=False, reason=f"judge-error: {exc}", confidence=0.0)

        try:
            data = json.loads(resp.choices[0].message.content or "{}")
            return RelevanceVerdict(
                relevant=bool(data.get("relevant")),
                reason=str(data.get("reason") or "no-reason"),
                confidence=float(data.get("confidence") or 0.0),
            )
        except (json.JSONDecodeError, ValueError, AttributeError) as exc:
            log.warning("relevance parse failed: %s", exc)
            return RelevanceVerdict(relevant=False, reason=f"parse-error: {exc}", confidence=0.0)
