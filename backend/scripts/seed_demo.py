"""Seed Acme Coffee demo data when database dependencies are configured."""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any


ACME_POSTS = [
    {
        "platform": "x",
        "external_id": "acme-x-1",
        "author_handle": "ios_buyer",
        "text": "Acme checkout crashed on iOS again, third time today",
        "url": "https://x.com/ios_buyer/status/acme-x-1",
        "sentiment": "negative",
    },
    {
        "platform": "reddit",
        "external_id": "acme-r-1",
        "author_handle": "u/cartlost",
        "text": "Acme app checkout is broken on iOS. Lost my cart twice.",
        "url": "https://reddit.com/r/acme/comments/acme-r-1",
        "sentiment": "negative",
    },
]


async def main() -> dict[str, Any]:
    try:
        import asyncpg
    except ImportError:
        return {
            "status": "skipped",
            "reason": "missing_dependency",
            "dependency": "asyncpg",
        }

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return {
            "status": "skipped",
            "reason": "missing_env",
            "env": "DATABASE_URL",
        }

    conn = await asyncpg.connect(database_url)
    try:
        brand_id = await conn.fetchval(
            """
            INSERT INTO brands (name, vertical, voice_guidelines, keywords)
            VALUES ('Acme Coffee', 'generic', 'Warm, direct, accountable.',
                    ARRAY['acme coffee','acme app','acme checkout'])
            ON CONFLICT DO NOTHING
            RETURNING id
            """
        )
        if brand_id is None:
            brand_id = await conn.fetchval("SELECT id FROM brands WHERE name='Acme Coffee'")

        cluster_id = await conn.fetchval(
            """
            INSERT INTO clusters
                (brand_id, name, summary, post_count, severity, severity_score,
                 tags, platforms, first_seen_at, last_activity_at)
            VALUES
                ($1, 'iOS checkout crash',
                 'Customers report checkout crashes in the Acme Coffee iOS app.',
                 12, 'critical', 820,
                 ARRAY['checkout','ios','crash'], ARRAY['x','reddit'], now(), now())
            RETURNING id
            """,
            brand_id,
        )
        await conn.execute(
            """
            INSERT INTO actions (brand_id, type, state, cluster_id, draft, context)
            VALUES
              ($1, 'response', 'pending', $2,
               '{"text":"We are investigating the iOS checkout crash and will update customers shortly."}'::jsonb,
               '{"cluster_summary":"iOS checkout crash","similar_report_count":12}'::jsonb),
              ($1, 'ticket', 'pending', $2,
               '{"title":"Fix iOS checkout crash","priority":"P1"}'::jsonb,
               '{"cluster_summary":"iOS checkout crash","similar_report_count":12}'::jsonb)
            """,
            brand_id,
            cluster_id,
        )
        return {
            "status": "seeded",
            "brand_id": str(brand_id),
            "cluster_id": str(cluster_id),
            "posts": len(ACME_POSTS),
            "seeded_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        await conn.close()


if __name__ == "__main__":
    print(asyncio.run(main()))
