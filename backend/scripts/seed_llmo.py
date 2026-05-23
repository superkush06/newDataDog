"""Seed demo LLMO ground truth and prompts when Postgres is configured."""
from __future__ import annotations

import asyncio
import os
from typing import Any


CROSBY = {
    "name": "Crosby",
    "ground_truth": (
        "Crosby is an AI-first law firm focused on contract review for startups. "
        "It combines licensed attorneys with AI-assisted workflows and is not a DIY SaaS tool."
    ),
    "competitors": ["Harvey AI", "Ironclad", "Robin AI", "Lawgeex"],
    "prompts": [
        ("What is Crosby AI?", "discovery"),
        ("Is Crosby a law firm or software?", "research"),
        ("Best AI legal services for startups", "discovery"),
    ],
}

ACME = {
    "name": "Acme Coffee",
    "ground_truth": (
        "Acme Coffee is a specialty coffee subscription with a mobile app for ordering, "
        "subscriptions, and rewards."
    ),
    "competitors": ["Trade Coffee", "Atlas Coffee", "Blue Bottle"],
    "prompts": [
        ("Best coffee subscription apps", "discovery"),
        ("Acme Coffee app reviews", "research"),
        ("Alternatives to Trade Coffee", "alternative"),
    ],
}


async def _seed_brand(conn: Any, data: dict[str, Any]) -> str:
    brand_id = await conn.fetchval(
        """
        INSERT INTO brands (name, vertical, voice_guidelines, keywords, ground_truth, competitors)
        VALUES ($1, 'generic', '', $2, $3, $4)
        ON CONFLICT DO NOTHING
        RETURNING id
        """,
        data["name"],
        [data["name"].lower()],
        data["ground_truth"],
        data["competitors"],
    )
    if brand_id is None:
        brand_id = await conn.fetchval("SELECT id FROM brands WHERE name=$1", data["name"])
        await conn.execute(
            "UPDATE brands SET ground_truth=$1, competitors=$2 WHERE id=$3",
            data["ground_truth"],
            data["competitors"],
            brand_id,
        )

    for prompt, intent in data["prompts"]:
        await conn.execute(
            """
            INSERT INTO brand_prompts (brand_id, prompt, intent)
            SELECT $1, $2, $3
            WHERE NOT EXISTS (
                SELECT 1 FROM brand_prompts WHERE brand_id=$1 AND prompt=$2
            )
            """,
            brand_id,
            prompt,
            intent,
        )
    return str(brand_id)


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
        return {"status": "skipped", "reason": "missing_env", "env": "DATABASE_URL"}

    conn = await asyncpg.connect(database_url)
    try:
        return {
            "status": "seeded",
            "brands": {
                "crosby": await _seed_brand(conn, CROSBY),
                "acme": await _seed_brand(conn, ACME),
            },
        }
    finally:
        await conn.close()


if __name__ == "__main__":
    print(asyncio.run(main()))
