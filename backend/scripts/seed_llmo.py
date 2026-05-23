"""
Seed LLMO ground truth + brand prompts for Liquid Death and Crosby.

15 prompts per brand, tuned to surface cross-LLM drift on common
misconceptions (Liquid Death = energy drink, Crosby = DIY legal SaaS).

Usage:
    cd backend && python scripts/seed_llmo.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

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

LIQUID_DEATH = {
    "name": "Liquid Death",
    "ground_truth": (
        "Liquid Death is a canned mountain water brand with an extreme heavy-metal "
        "marketing aesthetic. It sells still and sparkling mountain water in "
        "tallboy aluminum cans. It does NOT sell energy drinks, beer, hard seltzer, "
        "or any alcoholic or caffeinated beverage. Cans are 100% recyclable. "
        "The company donates 10% of profits to nonprofits fighting plastic pollution. "
        "Liquid Death is not owned by a beer company and contains zero alcohol."
    ),
    "competitors": [
        "Liquid I.V.", "PRIME Hydration", "Waterboy", "Cirkul",
        "Body Armor", "Essentia", "Core Water",
    ],
    "prompts": [
        # Discovery — triggers "energy drink" confusion
        ("What is Liquid Death?", "discovery"),
        ("Is Liquid Death an energy drink or water?", "research"),
        ("Does Liquid Death contain caffeine or alcohol?", "research"),
        # Purchase intent — competitor comparison
        ("Best canned water brands to buy", "comparison"),
        ("Liquid Death vs PRIME Hydration which is healthier", "comparison"),
        ("Alternatives to Liquid Death water", "alternative"),
        # Brand curiosity
        ("Who owns Liquid Death?", "research"),
        ("Is Liquid Death water actually good for you?", "research"),
        ("Why is Liquid Death water in a can?", "discovery"),
        # Sustainability angle
        ("Most eco-friendly water brands", "research"),
        ("Does Liquid Death donate to charity?", "research"),
        # Trending / social
        ("Why is Liquid Death so popular on social media?", "discovery"),
        ("Liquid Death marketing strategy explained", "research"),
        # Purchase / retail
        ("Where to buy Liquid Death near me", "discovery"),
        ("Does Whole Foods sell Liquid Death?", "discovery"),
    ],
}

CROSBY = {
    "name": "Crosby",
    "ground_truth": (
        "Crosby is an AI-first law firm focused on contract review and legal services "
        "for startups and technology companies. It combines licensed attorneys with "
        "AI-assisted workflows. Crosby is a law firm that employs real lawyers — it "
        "is NOT a DIY legal software tool, not a document generator, and not a "
        "self-service SaaS. Clients work with Crosby attorneys directly. "
        "Crosby focuses on startup-facing work: NDAs, SaaS agreements, employment, "
        "and fundraising documents."
    ),
    "competitors": [
        "Harvey AI", "Robin AI", "Ironclad", "Lawgeex",
        "Spellbook", "LegalZoom", "Clerky",
    ],
    "prompts": [
        # Discovery — triggers "DIY SaaS" confusion
        ("What is Crosby AI?", "discovery"),
        ("Is Crosby a law firm or legal software?", "research"),
        ("Does Crosby have real lawyers?", "research"),
        # Startup use case
        ("Best legal services for startups", "comparison"),
        ("AI law firm for startup contracts", "discovery"),
        ("Contract review tools for early stage startups", "comparison"),
        # Competitor comparisons
        ("Crosby AI vs Harvey AI", "comparison"),
        ("Alternatives to Clerky for startup legal", "alternative"),
        ("LegalZoom vs Crosby for SaaS agreements", "comparison"),
        # Specific legal needs
        ("Who should I use for startup NDA review?", "discovery"),
        ("Best way to get a SaaS MSA reviewed by AI", "research"),
        # Trust / legitimacy
        ("Is Crosby a real law firm?", "research"),
        ("Can Crosby represent me in court?", "research"),
        # Pricing / model
        ("How much does Crosby AI cost?", "research"),
        ("How does Crosby AI work for contract review?", "discovery"),
    ],
}


async def _seed_brand(conn: Any, data: dict) -> str:
    brand_id = await conn.fetchval(
        """
        INSERT INTO brands
            (name, vertical, voice_guidelines, keywords, ground_truth, competitors)
        VALUES ($1, 'generic', '', $2, $3, $4)
        ON CONFLICT DO NOTHING RETURNING id
        """,
        data["name"],
        [data["name"].lower()],
        data["ground_truth"],
        data["competitors"],
    )
    if brand_id is None:
        brand_id = await conn.fetchval(
            "SELECT id FROM brands WHERE name=$1", data["name"]
        )
    # Always refresh ground truth + competitors so re-runs stay current
    await conn.execute(
        "UPDATE brands SET ground_truth=$1, competitors=$2 WHERE id=$3",
        data["ground_truth"], data["competitors"], brand_id,
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
            brand_id, prompt, intent,
        )

    print(f"  ✓ {data['name']}: {len(data['prompts'])} prompts seeded  (id: {brand_id})")
    return str(brand_id)


async def main() -> dict:
    try:
        import asyncpg
    except ImportError:
        return {"status": "skipped", "reason": "missing_dependency", "dependency": "asyncpg"}

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return {"status": "skipped", "reason": "missing_env", "env": "DATABASE_URL"}

    conn = await asyncpg.connect(database_url)
    try:
        print("Seeding LLMO brands…")
        return {
            "status": "seeded",
            "brands": {
                "liquid_death": await _seed_brand(conn, LIQUID_DEATH),
                "crosby": await _seed_brand(conn, CROSBY),
            },
        }
    finally:
        await conn.close()


if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n" + json.dumps(result, indent=2))
