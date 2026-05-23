"""
X API v2 Filtered Stream consumer — forwards tweets to the Pulse webhook.

Run AFTER setup_x_stream.py. Keeps a persistent connection to the X stream
and POSTs each incoming tweet to the local Pulse backend as if it were a
real webhook delivery.

Usage:
    cd backend && python scripts/x_stream_consumer.py

Env required:
    X_BEARER_TOKEN       — X API bearer token
    X_WEBHOOK_SECRET     — HMAC secret (can be any string; must match backend config)
    PULSE_BRAND_ID       — UUID of the Liquid Death brand (printed by seed_demo.py)
    PULSE_API_URL        — defaults to http://localhost:8000
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import signal
import sys
import time
from pathlib import Path

import httpx

STREAM_URL = (
    "https://api.twitter.com/2/tweets/search/stream"
    "?tweet.fields=created_at,public_metrics,author_id,entities"
    "&expansions=author_id"
    "&user.fields=username,public_metrics"
)


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _forward(tweet: dict, brand_id: str, api_url: str, secret: str) -> None:
    """Normalise a raw X stream event into the shape the Pulse webhook expects."""
    data = tweet.get("data", {})
    includes = tweet.get("includes", {})
    users = {u["id"]: u for u in includes.get("users", [])}
    author = users.get(data.get("author_id", ""), {})
    metrics = data.get("public_metrics", {})

    payload = {
        "data": {
            "id": data.get("id", ""),
            "text": data.get("text", ""),
            "author_id": data.get("author_id", ""),
            "author": {
                "username": author.get("username", ""),
                "followers": (author.get("public_metrics") or {}).get("followers_count", 0),
            },
            "public_metrics": {
                "like_count": metrics.get("like_count", 0),
                "retweet_count": metrics.get("retweet_count", 0),
                "reply_count": metrics.get("reply_count", 0),
            },
            "created_at": data.get("created_at", ""),
        }
    }
    body = json.dumps(payload).encode()
    sig = _sign(body, secret) if secret else "sha256=demo"

    url = f"{api_url}/api/webhooks/x?brand_id={brand_id}"
    try:
        r = httpx.post(
            url, content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
            },
            timeout=10,
        )
        tweet_id = data.get("id", "?")
        text_preview = data.get("text", "")[:60]
        print(f"  → tweet {tweet_id}: {text_preview!r}  [{r.status_code}]")
    except Exception as e:
        print(f"  ✗ forward failed: {e}")


def stream(token: str, brand_id: str, api_url: str, secret: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Connecting to X filtered stream…")
    print(f"Forwarding to {api_url}/api/webhooks/x?brand_id={brand_id}")
    print("Press Ctrl+C to stop.\n")

    with httpx.stream("GET", STREAM_URL, headers=headers, timeout=None) as r:
        if r.status_code != 200:
            print(f"ERROR: stream returned {r.status_code}")
            print(r.text)
            sys.exit(1)

        for line in r.iter_lines():
            line = line.strip()
            if not line:
                continue  # keepalive newline
            try:
                tweet = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "data" in tweet:
                _forward(tweet, brand_id, api_url, secret)


def main() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    token = os.environ.get("X_BEARER_TOKEN")
    brand_id = os.environ.get("PULSE_BRAND_ID", "")
    api_url = os.environ.get("PULSE_API_URL", "http://localhost:8000")
    secret = os.environ.get("X_WEBHOOK_SECRET", "demo-secret")

    if not token:
        print("ERROR: X_BEARER_TOKEN not set")
        sys.exit(1)
    if not brand_id:
        print("ERROR: PULSE_BRAND_ID not set — run seed_demo.py first and copy the brand_id")
        sys.exit(1)

    # Reconnect on disconnect with backoff (streams occasionally drop)
    backoff = 5
    while True:
        try:
            stream(token, brand_id, api_url, secret)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"Stream error: {e}. Reconnecting in {backoff}s…")
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)


if __name__ == "__main__":
    main()
