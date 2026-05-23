"""
Set up X API v2 Filtered Stream rules for the Liquid Death demo.

Requires: X_BEARER_TOKEN in .env (Basic access or higher on developer.twitter.com)

What this does:
  1. Deletes any existing stream rules for this project (clean slate)
  2. Adds a rule that catches tweets mentioning Liquid Death keywords
  3. Prints the rule ID — keep it, you may need it to delete later

Usage:
    cd backend && python scripts/setup_x_stream.py

X API note:
    Filtered Stream requires Basic access ($100/mo) or Elevated (free apply).
    Free tier only gets search/recent (polling). If you don't have stream access,
    use demo_inject.py instead — it achieves the same demo effect.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

STREAM_RULES_URL = "https://api.twitter.com/2/tweets/search/stream/rules"

# Catches tweets mentioning Liquid Death directly or indirectly
# Uses X operator syntax: https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/integrate/build-a-rule
RULES = [
    {
        "value": (
            "(\"liquid death\" OR \"liquiddeathwater\" OR \"@liquiddeathwater\" "
            "OR \"murder your thirst\" OR \"liquid death water\") "
            "-is:retweet lang:en"
        ),
        "tag": "liquid-death-demo",
    }
]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_existing_rules(token: str) -> list[dict]:
    r = httpx.get(STREAM_RULES_URL, headers=_headers(token))
    r.raise_for_status()
    return r.json().get("data", []) or []


def _delete_rules(token: str, ids: list[str]) -> None:
    if not ids:
        return
    r = httpx.post(
        STREAM_RULES_URL,
        headers=_headers(token),
        json={"delete": {"ids": ids}},
    )
    r.raise_for_status()
    print(f"  Deleted {len(ids)} old rule(s)")


def _add_rules(token: str, rules: list[dict]) -> list[dict]:
    r = httpx.post(
        STREAM_RULES_URL,
        headers=_headers(token),
        json={"add": rules},
    )
    r.raise_for_status()
    return r.json().get("data", []) or []


def main() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    token = os.environ.get("X_BEARER_TOKEN")
    if not token:
        print("ERROR: X_BEARER_TOKEN not set in .env")
        sys.exit(1)

    print("Fetching existing stream rules…")
    existing = _get_existing_rules(token)
    if existing:
        print(f"  Found {len(existing)} existing rule(s): {[r['tag'] for r in existing]}")
        _delete_rules(token, [r["id"] for r in existing])
    else:
        print("  No existing rules.")

    print("Adding Liquid Death stream rule…")
    added = _add_rules(token, RULES)
    for rule in added:
        print(f"  ✓ Rule added — id: {rule['id']}  tag: {rule.get('tag', '')}")
        print(f"    value: {rule['value']}")

    print("\nDone. Now run x_stream_consumer.py to start receiving tweets.")


if __name__ == "__main__":
    main()
