"""
Seed Liquid Death demo data.

Creates the brand, inserts 12 staged posts (X + Reddit) that form a
Critical cluster around a canned-water shortage complaint spike, then
seeds the cluster + pending actions so the dashboard is live on first load.

Usage:
    cd backend && python scripts/seed_demo.py

Env required: DATABASE_URL, CLICKHOUSE_HOST/PORT/USER/PASSWORD
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load global .env at repo root + ensure macOS Python uses certifi CA bundle.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
if not os.environ.get("SSL_CERT_FILE"):
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    except ImportError:
        pass

# ---------------------------------------------------------------------------
# Brand config
# ---------------------------------------------------------------------------

BRAND = {
    "name": "Liquid Death",
    "vertical": "generic",
    "voice_guidelines": (
        "Irreverent, punk-rock, self-aware. Never corporate. "
        "Owns mistakes with dark humor. Short sentences. No em dashes."
    ),
    "keywords": [
        "liquid death", "liquiddeathwater", "murder your thirst",
        "@liquiddeathwater", "liquid death water",
    ],
    "ground_truth": (
        "Liquid Death is a canned mountain water brand known for its extreme "
        "marketing and heavy-metal aesthetic. It sells still and sparkling water "
        "in tallboy cans. It does NOT sell energy drinks, beer, or any alcoholic "
        "beverage. Cans are 100% recyclable aluminum. The company donates 10% of "
        "profits to charity."
    ),
    "competitors": ["Liquid I.V.", "Waterboy", "Cirkul", "PRIME Hydration", "Body Armor"],
    "thresholds": {"critical": 700, "high": 400, "medium": 200},
    "connections": {},
}

# ---------------------------------------------------------------------------
# Staged posts — 12 posts across X and Reddit forming a shortage + can
# quality cluster. Designed to score Critical.
# ---------------------------------------------------------------------------

BASE_TIME = datetime.now(timezone.utc) - timedelta(hours=3)


def t(offset_min: int) -> str:
    return (BASE_TIME + timedelta(minutes=offset_min)).isoformat()


POSTS = [
    # X — high engagement, kicks off the cluster
    dict(
        platform="x", platform_post_id="ld-x-001",
        author_handle="@deathcult_kyle", author_follower_count=84_200,
        text="@liquiddeathwater three Whole Foods near me are completely out of stock. "
             "been out for 2 weeks. what is going on with your supply chain??",
        likes=1_840, shares=620, comments=94,
        permalink="https://x.com/deathcult_kyle/status/ld-x-001",
        posted_at=t(0), sentiment="negative",
    ),
    dict(
        platform="x", platform_post_id="ld-x-002",
        author_handle="@fitnessfreak_mara", author_follower_count=12_500,
        text="liquid death cans taste metallic now?? ordered a 12-pack and half "
             "of them had this weird aftertaste. switching to something else if this keeps up",
        likes=430, shares=88, comments=41,
        permalink="https://x.com/fitnessfreak_mara/status/ld-x-002",
        posted_at=t(12), sentiment="negative",
    ),
    dict(
        platform="x", platform_post_id="ld-x-003",
        author_handle="@gymrat_dan", author_follower_count=3_200,
        text="ok so @liquiddeathwater is out EVERYWHERE in los angeles. "
             "checked 6 stores. just restocked with PRIME and honestly not mad about it",
        likes=290, shares=45, comments=22,
        permalink="https://x.com/gymrat_dan/status/ld-x-003",
        posted_at=t(18), sentiment="negative",
    ),
    dict(
        platform="x", platform_post_id="ld-x-004",
        author_handle="@veganrunner_tj", author_follower_count=7_800,
        text="love the brand but the metallic taste issue in the new cans is real. "
             "checked liquid death subreddit and i'm not alone. @liquiddeathwater please respond",
        likes=560, shares=130, comments=67,
        permalink="https://x.com/veganrunner_tj/status/ld-x-004",
        posted_at=t(25), sentiment="negative",
    ),
    dict(
        platform="x", platform_post_id="ld-x-005",
        author_handle="@metalpunk_sarah", author_follower_count=218_000,
        text="the liquid death supply chain is collapsing and nobody is talking about it. "
             "3 distribution centers reportedly paused. thread 🧵",
        likes=4_200, shares=1_850, comments=312,
        permalink="https://x.com/metalpunk_sarah/status/ld-x-005",
        posted_at=t(31), sentiment="negative",
    ),
    dict(
        platform="x", platform_post_id="ld-x-006",
        author_handle="@thirsty_mike_nyc", author_follower_count=900,
        text="is @liquiddeathwater aware that their cans have a metallic taste lately? "
             "bought from amazon, same issue. batch number on the bottom is 24B-11",
        likes=82, shares=14, comments=9,
        permalink="https://x.com/thirsty_mike_nyc/status/ld-x-006",
        posted_at=t(38), sentiment="question",
    ),
    dict(
        platform="x", platform_post_id="ld-x-007",
        author_handle="@wholesomehike_co", author_follower_count=5_100,
        text="@liquiddeathwater please explain the metallic can situation. "
             "health concern or just bad batch? need to know if i should throw out my supply",
        likes=190, shares=28, comments=18,
        permalink="https://x.com/wholesomehike_co/status/ld-x-007",
        posted_at=t(44), sentiment="question",
    ),
    # Reddit — adds volume + negative sentiment
    dict(
        platform="reddit", platform_post_id="ld-r-001",
        author_handle="u/hydration_nerd", author_follower_count=0,
        text="[r/LiquidDeath] PSA: Metallic taste in recent cans — batch 24B-11 "
             "confirmed by 40+ commenters. Has anyone contacted Liquid Death support? "
             "No response on social yet. This is a real issue.",
        likes=1_120, shares=0, comments=214,
        permalink="https://reddit.com/r/LiquidDeath/comments/ld-r-001",
        posted_at=t(55), sentiment="negative",
    ),
    dict(
        platform="reddit", platform_post_id="ld-r-002",
        author_handle="u/can_connoisseur", author_follower_count=0,
        text="Switched from Liquid Death after the taste issue. Tried 3 different "
             "cans from 2 different stores. All batch 24B. Something changed in the "
             "canning process. Moved to still water in glass for now.",
        likes=780, shares=0, comments=89,
        permalink="https://reddit.com/r/LiquidDeath/comments/ld-r-002",
        posted_at=t(65), sentiment="negative",
    ),
    dict(
        platform="reddit", platform_post_id="ld-r-003",
        author_handle="u/supply_chain_watcher", author_follower_count=0,
        text="Liquid Death stockouts are regional but severe. LA, NYC, Chicago all "
             "reporting empty shelves. The metallic taste reports and the supply issues "
             "might be related — rushed production run?",
        likes=540, shares=0, comments=61,
        permalink="https://reddit.com/r/LiquidDeath/comments/ld-r-003",
        posted_at=t(72), sentiment="negative",
    ),
    dict(
        platform="reddit", platform_post_id="ld-r-004",
        author_handle="u/former_ld_fan", author_follower_count=0,
        text="I reached out to Liquid Death support 5 days ago about the metallic taste. "
             "No response. Their Twitter is silent. This is how you lose loyal customers.",
        likes=920, shares=0, comments=143,
        permalink="https://reddit.com/r/LiquidDeath/comments/ld-r-004",
        posted_at=t(80), sentiment="negative",
    ),
    dict(
        platform="reddit", platform_post_id="ld-r-005",
        author_handle="u/concerned_parent_pdx", author_follower_count=0,
        text="My kids drink Liquid Death. The metallic taste has me worried about "
             "can lining. Is this a BPA thing? Does anyone know if batch 24B-11 is "
             "being recalled? Very concerned.",
        likes=670, shares=0, comments=98,
        permalink="https://reddit.com/r/LiquidDeath/comments/ld-r-005",
        posted_at=t(87), sentiment="negative",
    ),
]

# Precomputed severity (would normally come from the score pipeline)
CLUSTER = {
    "name": "Metallic taste + stockout — Batch 24B-11",
    "summary": (
        "Customers across LA, NYC, and Chicago report a metallic aftertaste in "
        "Liquid Death cans from batch 24B-11, coinciding with regional stockouts. "
        "No official response from the brand after 5+ days. A high-follower Twitter "
        "thread is amplifying the issue. A concerned parent community segment is "
        "raising health-safety framing."
    ),
    "severity": "critical",
    "severity_score": 1_140.0,
    "tags": ["metallic-taste", "batch-24B", "stockout", "supply-chain", "health-concern"],
    "platforms": ["x", "reddit"],
    "post_count": 12,
}

ACTIONS = [
    {
        "type": "response",
        "draft": {
            "text": (
                "We hear you — and we're investigating batch 24B-11 right now. "
                "If you got a can that tastes off, email murder@liquiddeath.com "
                "with your batch number and we'll make it right. No corporate runaround. "
                "Update coming in 24h."
            ),
            "char_count": 232,
            "char_limit": 280,
            "platform": "x",
        },
        "context": {
            "cluster_summary": CLUSTER["summary"],
            "original_post_text": POSTS[4]["text"],
            "similar_report_count": 12,
        },
    },
    {
        "type": "ticket",
        "draft": {
            "title": "[P1] Metallic taste report — Batch 24B-11 can lining investigation",
            "description": (
                "12 social reports (X + Reddit) of metallic taste in batch 24B-11 cans. "
                "Regional stockouts across LA/NYC/Chicago may indicate a rushed production "
                "run. A parent-community segment is raising health-safety framing — "
                "potential recall risk if unaddressed. 5-day response gap already visible."
            ),
            "priority": "P1 (score: 1140)",
            "social_links": [p["permalink"] for p in POSTS[:5]],
        },
        "context": {
            "cluster_summary": CLUSTER["summary"],
            "similar_report_count": 12,
        },
    },
    {
        "type": "escalation",
        "draft": {
            "channel": "#brand-crisis",
            "summary": CLUSTER["summary"],
            "top_posts": [p["permalink"] for p in POSTS[:5]],
            "recommended_actions": [
                "Issue a holding statement on @liquiddeathwater Twitter within 2h",
                "Pull batch 24B-11 from e-commerce fulfillment pending QA review",
                "Open war room with supply chain + QA teams",
            ],
        },
        "context": {
            "cluster_summary": CLUSTER["summary"],
            "similar_report_count": 12,
        },
    },
]


# ---------------------------------------------------------------------------
# DB writes
# ---------------------------------------------------------------------------

async def main() -> dict:
    try:
        import asyncpg
        import clickhouse_connect
    except ImportError as e:
        return {"status": "skipped", "reason": "missing_dependency", "detail": str(e)}

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return {"status": "skipped", "reason": "missing_env", "env": "DATABASE_URL"}

    pg = await asyncpg.connect(database_url)
    try:
        # --- brand ---
        brand_id = await pg.fetchval(
            """
            INSERT INTO brands
                (name, vertical, voice_guidelines, keywords, thresholds,
                 connections, ground_truth, competitors)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8)
            ON CONFLICT DO NOTHING RETURNING id
            """,
            BRAND["name"], BRAND["vertical"], BRAND["voice_guidelines"],
            BRAND["keywords"],
            json.dumps(BRAND["thresholds"]), json.dumps(BRAND["connections"]),
            BRAND["ground_truth"], BRAND["competitors"],
        )
        if brand_id is None:
            brand_id = await pg.fetchval(
                "SELECT id FROM brands WHERE name=$1", BRAND["name"]
            )
            # refresh ground_truth and competitors in case they were stale
            await pg.execute(
                "UPDATE brands SET ground_truth=$1, competitors=$2, keywords=$3 WHERE id=$4",
                BRAND["ground_truth"], BRAND["competitors"],
                BRAND["keywords"], brand_id,
            )

        brand_id_str = str(brand_id)
        print(f"✓ Brand: Liquid Death  ({brand_id_str})")

        # --- cluster ---
        cluster_id = await pg.fetchval(
            """
            INSERT INTO clusters
                (brand_id, name, summary, post_count, severity, severity_score,
                 tags, platforms, first_seen_at, last_activity_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8, now() - interval '3 hours', now())
            RETURNING id
            """,
            brand_id,
            CLUSTER["name"], CLUSTER["summary"], CLUSTER["post_count"],
            CLUSTER["severity"], CLUSTER["severity_score"],
            CLUSTER["tags"], CLUSTER["platforms"],
        )
        cluster_id_str = str(cluster_id)
        print(f"✓ Cluster: {CLUSTER['name']}  ({cluster_id_str})")

        # --- actions ---
        for action in ACTIONS:
            await pg.execute(
                """
                INSERT INTO actions
                    (brand_id, type, state, cluster_id, draft, context)
                VALUES ($1,$2,'pending',$3,$4::jsonb,$5::jsonb)
                """,
                brand_id, action["type"], cluster_id,
                json.dumps(action["draft"]), json.dumps(action["context"]),
            )
        print(f"✓ Actions: response + ticket + escalation (all pending)")

        # --- posts into ClickHouse ---
        ch_host = os.environ.get("CLICKHOUSE_HOST")
        if ch_host:
            client = clickhouse_connect.get_client(
                host=ch_host,
                port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
                username=os.environ.get("CLICKHOUSE_USER", "default"),
                password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
                secure=True,
            )
            rows = []
            for p in POSTS:
                rows.append([
                    str(uuid.uuid4()), brand_id_str,
                    p["platform"], p["platform_post_id"],
                    p["author_handle"], p["author_follower_count"],
                    p["text"], [],
                    p["likes"], p["shares"], p["comments"],
                    p["permalink"],
                    datetime.fromisoformat(p["posted_at"]),
                    datetime.now(timezone.utc),
                    p["sentiment"], cluster_id_str, "seed",
                ])
            client.insert(
                "posts", rows,
                column_names=[
                    "id", "brand_id", "platform", "platform_post_id",
                    "author_handle", "author_follower_count", "text", "media_urls",
                    "likes", "shares", "comments", "permalink",
                    "posted_at", "ingested_at", "sentiment", "cluster_id", "source",
                ],
            )
            print(f"✓ ClickHouse: {len(POSTS)} posts inserted")
        else:
            print("⚠  ClickHouse skipped (CLICKHOUSE_HOST not set)")

        return {
            "status": "seeded",
            "brand": "Liquid Death",
            "brand_id": brand_id_str,
            "cluster_id": cluster_id_str,
            "posts": len(POSTS),
        }

    finally:
        await pg.close()


if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n" + json.dumps(result, indent=2))
