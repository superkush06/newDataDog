"""
Demo injector — fires pre-written Liquid Death tweets through the local
Pulse webhook endpoint, simulating live X ingest without needing a real
stream connection.

Use this as your demo fallback (or primary if you don't have X Basic access).
Injects tweets one at a time with a configurable delay so the dashboard
updates visibly during the presentation.

Usage:
    # Inject all tweets with 4-second gap (default):
    cd backend && python scripts/demo_inject.py

    # Faster (good for testing):
    cd backend && python scripts/demo_inject.py --delay 1

    # Single tweet by index (0-based):
    cd backend && python scripts/demo_inject.py --index 4

Env required:
    PULSE_BRAND_ID   — UUID of the Liquid Death brand (from seed_demo.py output)
    X_WEBHOOK_SECRET — must match backend config (can be any string in dev)
    PULSE_API_URL    — defaults to http://localhost:8000
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Demo tweet scripts — ordered for maximum narrative impact
# ---------------------------------------------------------------------------

TWEETS = [
    # 1. Influential user fires the opening shot
    {
        "id": "demo-ld-1001",
        "text": "@liquiddeathwater three Whole Foods near me are completely out of stock. "
                "been out for 2 weeks. what is going on with your supply chain??",
        "username": "deathcult_kyle",
        "followers": 84_200,
        "likes": 1_840, "retweets": 620, "replies": 94,
        "label": "HIGH-FOLLOWER — supply chain complaint",
    },
    # 2. Taste issue surfaces
    {
        "id": "demo-ld-1002",
        "text": "liquid death cans taste metallic now?? ordered a 12-pack and half "
                "of them had this weird aftertaste. switching to something else if this keeps up",
        "username": "fitnessfreak_mara",
        "followers": 12_500,
        "likes": 430, "retweets": 88, "replies": 41,
        "label": "metallic taste complaint",
    },
    # 3. Stock confirmation from another city
    {
        "id": "demo-ld-1003",
        "text": "ok so @liquiddeathwater is out EVERYWHERE in los angeles. "
                "checked 6 stores. just restocked with PRIME and honestly not mad",
        "username": "gymrat_dan",
        "followers": 3_200,
        "likes": 290, "retweets": 45, "replies": 22,
        "label": "stockout — LA",
    },
    # 4. Cross-platform validation
    {
        "id": "demo-ld-1004",
        "text": "love the brand but the metallic taste issue in the new cans is real. "
                "checked liquid death subreddit and i'm not alone. @liquiddeathwater please respond",
        "username": "veganrunner_tj",
        "followers": 7_800,
        "likes": 560, "retweets": 130, "replies": 67,
        "label": "cross-platform — reddit confirmation",
    },
    # 5. Mega-thread from high-follower — this is the scoring spike
    {
        "id": "demo-ld-1005",
        "text": "the liquid death supply chain is collapsing and nobody is talking about it. "
                "3 distribution centers reportedly paused. batch 24B-11 is the problem. thread 🧵",
        "username": "metalpunk_sarah",
        "followers": 218_000,
        "likes": 4_200, "retweets": 1_850, "replies": 312,
        "label": "VIRAL THREAD — 218K followers — scoring spike to Critical",
    },
    # 6. Health concern framing — escalation trigger
    {
        "id": "demo-ld-1006",
        "text": "My kids drink Liquid Death. The metallic taste has me worried about "
                "can lining. Is this a BPA thing? batch 24B-11 recall??",
        "username": "concerned_parent_pdx",
        "followers": 2_100,
        "likes": 670, "retweets": 0, "replies": 98,
        "label": "health-concern framing — escalation signal",
    },
    # 7. Direct question to brand
    {
        "id": "demo-ld-1007",
        "text": "@liquiddeathwater please explain the metallic can situation. "
                "health concern or just bad batch? need to know if i should throw out my supply",
        "username": "wholesomehike_co",
        "followers": 5_100,
        "likes": 190, "retweets": 28, "replies": 18,
        "label": "direct brand question — response action trigger",
    },
]


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _build_payload(tweet: dict) -> dict:
    return {
        "data": {
            "id": tweet["id"],
            "text": tweet["text"],
            "author_id": tweet["username"],
            "author": {
                "username": tweet["username"],
                "followers": tweet["followers"],
            },
            "public_metrics": {
                "like_count": tweet["likes"],
                "retweet_count": tweet["retweets"],
                "reply_count": tweet["replies"],
            },
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    }


def inject(
    tweet: dict, brand_id: str, api_url: str, secret: str, index: int
) -> None:
    payload = _build_payload(tweet)
    body = json.dumps(payload).encode()
    sig = _sign(body, secret)

    url = f"{api_url}/api/webhooks/x?brand_id={brand_id}"
    print(f"\n[{index+1}/{len(TWEETS)}] {tweet['label']}")
    print(f"  @{tweet['username']} ({tweet['followers']:,} followers)")
    print(f"  \"{tweet['text'][:80]}{'…' if len(tweet['text']) > 80 else ''}\"")

    try:
        r = httpx.post(
            url, content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
            },
            timeout=10,
        )
        status = "✓" if r.status_code in (200, 202) else "✗"
        print(f"  {status} backend returned {r.status_code}")
    except Exception as e:
        print(f"  ✗ failed: {e} — is the backend running?")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject demo tweets into Pulse")
    parser.add_argument("--delay", type=float, default=4.0,
                        help="Seconds between tweets (default: 4)")
    parser.add_argument("--index", type=int, default=None,
                        help="Inject a single tweet by 0-based index")
    args = parser.parse_args()

    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    brand_id = os.environ.get("PULSE_BRAND_ID", "")
    api_url = os.environ.get("PULSE_API_URL", "http://localhost:8000")
    secret = os.environ.get("X_WEBHOOK_SECRET", "demo-secret")

    if not brand_id:
        print("ERROR: PULSE_BRAND_ID not set.")
        print("  Run: python scripts/seed_demo.py  and copy the brand_id from the output.")
        return

    if args.index is not None:
        if 0 <= args.index < len(TWEETS):
            inject(TWEETS[args.index], brand_id, api_url, secret, args.index)
        else:
            print(f"ERROR: --index must be 0–{len(TWEETS)-1}")
        return

    print(f"Injecting {len(TWEETS)} demo tweets → {api_url}")
    print(f"Brand ID: {brand_id}")
    print(f"Delay: {args.delay}s between tweets")
    print("=" * 60)

    for i, tweet in enumerate(TWEETS):
        inject(tweet, brand_id, api_url, secret, i)
        if i < len(TWEETS) - 1:
            time.sleep(args.delay)

    print("\n" + "=" * 60)
    print("Done. Check the dashboard at http://localhost:3000/dashboard")
    print("  → /feed      should show all 7 posts")
    print("  → /clusters  should show a Critical cluster")
    print("  → /actions   should show 3 pending actions")


if __name__ == "__main__":
    main()
