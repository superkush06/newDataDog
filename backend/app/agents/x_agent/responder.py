"""Groq-backed reply generator. Produces a concise, human-sounding reply that
acknowledges the tweet without sounding scripted."""
from __future__ import annotations

import logging
import random

from groq import Groq

from .config import XAgentConfig
from .monitor import Tweet

log = logging.getLogger("x_agent.responder")


_SYSTEM = """You write public replies on X for Crosby — an AI-first law firm.

You are responding directly to a tweet. Rules:
- 1 to 2 short sentences, under 240 characters total
- Sound human and confident, never corporate or robotic
- Reference the specific issue in the tweet, do not paraphrase it back wholesale
- Communicate something like: "we're aware and looking into it" / "this will be addressed" / "will handle this shortly" — but VARY the wording, never repeat a template
- No hashtags, no emojis, no @mentions (the platform handles the reply chain)
- No promises of timelines you can't keep ("within the hour", etc.)
- No links
- No quoting the original tweet
- Plain text only. No markdown.

Return ONLY the reply text. No quotes, no preamble, no explanation."""


_FALLBACK_REPLIES = [
    "On it — looking into this now and will follow up shortly.",
    "Thanks for flagging — we're aware and working through it.",
    "Appreciate the heads up. Handling it now.",
    "Got it — this will be addressed.",
    "We see this — digging in and circling back.",
]


class GroqResponder:
    def __init__(self, cfg: XAgentConfig) -> None:
        self.cfg = cfg
        self._client = Groq(api_key=cfg.groq_api_key) if cfg.groq_api_key else None

    def generate(self, tweet: Tweet, thread_context: str | None) -> str:
        if not self._client:
            log.warning("no groq client — using static fallback")
            return random.choice(_FALLBACK_REPLIES)

        user_msg = f"Tweet to reply to: {tweet.text}\n"
        if thread_context:
            user_msg += f"Parent tweet (for context): {thread_context}\n"
        user_msg += "\nWrite the reply now."

        try:
            resp = self._client.chat.completions.create(
                model=self.cfg.groq_model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.8,
                max_tokens=120,
                top_p=0.9,
            )
            text = (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            log.warning("groq generation failed: %s — falling back", exc)
            return random.choice(_FALLBACK_REPLIES)

        # Strip wrapping quotes the model sometimes adds
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'", "`"}:
            text = text[1:-1].strip()

        # Hard cap at 240 chars to stay well clear of the 280 limit
        if len(text) > 240:
            text = text[:237].rsplit(" ", 1)[0] + "..."

        if not text:
            return random.choice(_FALLBACK_REPLIES)
        return text
