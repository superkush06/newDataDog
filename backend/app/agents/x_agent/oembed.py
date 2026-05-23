"""Free, unauthenticated tweet content fetch via X's public syndication endpoint.

We bypass the paywalled v2 read API by hitting the same syndication endpoint
that powers x.com / twitter.com embed widgets across the web. No auth, no
rate-credit pool, no developer portal involvement.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import requests

log = logging.getLogger("x_agent.oembed")

_TID_PATTERNS = [
    re.compile(r"(?:twitter|x)\.com/[^/]+/status(?:es)?/(\d+)"),
    re.compile(r"^\s*(\d{6,25})\s*$"),  # raw numeric id
]


def extract_tweet_id(url_or_id: str) -> str | None:
    """Pull the numeric tweet id out of a URL, raw id, or copy-paste blob."""
    for pat in _TID_PATTERNS:
        m = pat.search(url_or_id)
        if m:
            return m.group(1)
    return None


@dataclass
class FetchedTweet:
    id: str
    author_handle: str
    text: str
    created_at: str | None
    in_reply_to_id: str | None


def fetch_tweet(tweet_id: str) -> FetchedTweet | None:
    """Return tweet text/author/replied-to via the syndication endpoint."""
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=x"
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        log.warning("syndication request failed: %s", exc)
        return None

    if r.status_code == 404:
        log.warning("tweet %s not found (deleted / private / wrong id)", tweet_id)
        return None
    if r.status_code >= 400:
        log.warning("syndication HTTP %s for %s", r.status_code, tweet_id)
        return None

    # When the endpoint serves JSON (the default path for live public tweets)
    # the body is a plain JSON object. The HTML fallback only fires on errors.
    try:
        data = r.json()
    except ValueError:
        log.warning("syndication returned non-JSON for %s", tweet_id)
        return None

    handle = (data.get("user") or {}).get("screen_name") or ""
    return FetchedTweet(
        id=str(data.get("id_str") or tweet_id),
        author_handle=handle,
        text=data.get("text") or "",
        created_at=data.get("created_at"),
        in_reply_to_id=data.get("in_reply_to_status_id_str"),
    )
