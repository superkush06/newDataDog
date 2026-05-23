"""Populate the Crosby live feed with realistic Reddit chatter for the demo.

Idempotent — ReplacingMergeTree on (brand_id, platform, platform_post_id)
collapses duplicates on rerun. ingested_at is staggered so the most recent
rows look like they just landed; the dashboard's 30s poll will reveal them
as if the Nimble adapter is live.
"""
from __future__ import annotations

import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    pass

import clickhouse_connect


BRAND_ID = os.environ.get("NEXT_PUBLIC_DEMO_BRAND_ID")


POSTS = [
    # ─── recent / fresh (will appear "seconds ago" via staggered ingested_at) ──
    {
        "sub": "lawyertalk",
        "author": "u/contract_grinder",
        "text": "Tried Crosby for redlining an NDA last night. Spit back a clean markup in under a minute and flagged a sneaky IP assignment clause my partner missed. Genuinely impressed.",
        "sentiment": "positive",
        "likes": 247, "comments": 38,
        "slug": "crosby_nda_redline_actually_useful",
    },
    {
        "sub": "biglaw",
        "author": "u/midlaw_associate",
        "text": "Anyone else's firm piloting Crosby? Partners are pushing it hard but I'm worried about billable hour erosion. Diligence memo that took me 6 hours took it 11 minutes.",
        "sentiment": "neutral",
        "likes": 412, "comments": 156,
        "slug": "crosby_pilot_billable_hours_question",
    },
    {
        "sub": "legaltech",
        "author": "u/legalops_lead",
        "text": "Switched our in-house contract review stack from Ironclad + Spellbook to Crosby last month. Throughput up ~3x. The agent UX is night and day vs. the form-based competitors.",
        "sentiment": "positive",
        "likes": 189, "comments": 22,
        "slug": "crosby_vs_ironclad_spellbook_review",
    },
    {
        "sub": "Entrepreneur",
        "author": "u/seed_founder_2024",
        "text": "Used Crosby to negotiate my SAFE round. It caught a non-standard MFN provision the investor's counsel had buried in the side letter. Saved me probably 2-3% dilution.",
        "sentiment": "positive",
        "likes": 521, "comments": 73,
        "slug": "crosby_caught_mfn_safe_round",
    },

    # ─── 5 min to a few hours old ────────────────────────────────────────────
    {
        "sub": "Lawyertalk",
        "author": "u/skeptical_4th_year",
        "text": "Crosby keeps confidently citing case law that doesn't exist. Twice this week. Are we sure this is ready for substantive work or is this still a fancy autocomplete?",
        "sentiment": "negative",
        "likes": 308, "comments": 191,
        "slug": "crosby_hallucinated_citations_again",
    },
    {
        "sub": "LawSchool",
        "author": "u/2L_at_t14",
        "text": "Just sat through a panel where a Crosby PM demoed the agent live. It drafted a motion to compel in real time and explained its reasoning at each step. Genuinely the first AI legal tool that didn't feel like vaporware.",
        "sentiment": "positive",
        "likes": 167, "comments": 41,
        "slug": "crosby_demo_motion_to_compel",
    },
    {
        "sub": "legaltech",
        "author": "u/v_lattimer",
        "text": "Crosby's pricing page is opaque on purpose. We spent two weeks on procurement and the per-seat number we landed on is wildly higher than what's implied publicly. Watch out.",
        "sentiment": "negative",
        "likes": 94, "comments": 47,
        "slug": "crosby_opaque_enterprise_pricing",
    },
    {
        "sub": "startups",
        "author": "u/yc_w24",
        "text": "Genuine question: is Crosby just GPT-4 + a system prompt + a Notion integration? I want to believe it's more but every workflow I've seen could be replicated with a half-decent agent harness.",
        "sentiment": "question",
        "likes": 78, "comments": 134,
        "slug": "crosby_actually_differentiated_question",
    },
    {
        "sub": "ChatGPTPro",
        "author": "u/promptengineer_99",
        "text": "Side-by-side: Crosby vs. raw o1 + a 12k token system prompt on a M&A diligence task. Crosby was clearly fine-tuned on legal corpora — the citation discipline alone is a different league.",
        "sentiment": "positive",
        "likes": 612, "comments": 88,
        "slug": "crosby_vs_o1_diligence_bench",
    },
    {
        "sub": "Lawyertalk",
        "author": "u/pi_attorney",
        "text": "Crosby is great for transactional. Don't bother for litigation — discovery review still needs a human and the deposition prep features are half-baked.",
        "sentiment": "neutral",
        "likes": 156, "comments": 29,
        "slug": "crosby_transactional_yes_litigation_no",
    },

    # ─── older / archival depth ──────────────────────────────────────────────
    {
        "sub": "biglaw",
        "author": "u/cravath_refugee",
        "text": "Heard the Crosby founders pitched our managing partner. Equity-light deal, full firm rollout in 90 days. Insane velocity for a firm that took 4 years to adopt e-signature.",
        "sentiment": "neutral",
        "likes": 234, "comments": 67,
        "slug": "crosby_pitched_our_managing_partner",
    },
    {
        "sub": "legaltech",
        "author": "u/harvey_pm_left",
        "text": "Worked at Harvey before joining Crosby's design partner program. The product philosophy is different — Crosby treats every interaction as agentic, Harvey is still chat-first. Big delta on outcomes.",
        "sentiment": "positive",
        "likes": 401, "comments": 112,
        "slug": "harvey_vs_crosby_design_partner",
    },
    {
        "sub": "Lawyertalk",
        "author": "u/in_house_counsel_42",
        "text": "Anyone have a Crosby coupon? Renewal is up and my CFO is questioning the line item. We use it daily but the price increase YoY is hard to justify.",
        "sentiment": "question",
        "likes": 22, "comments": 14,
        "slug": "crosby_renewal_price_increase_coupon",
    },
    {
        "sub": "Entrepreneur",
        "author": "u/closed_series_a",
        "text": "Crosby reviewed our term sheet and flagged a liquidation preference detail I'd glossed over. My lawyer was pissed (rightly — he should have caught it). Tool more than paid for itself in one session.",
        "sentiment": "positive",
        "likes": 287, "comments": 51,
        "slug": "crosby_caught_liq_pref_term_sheet",
    },
    {
        "sub": "SmallBusiness",
        "author": "u/coffeeshop_owner_pa",
        "text": "Used Crosby for a commercial lease negotiation. Saved me $4200/yr in CAM charges by spotting language my landlord's attorney used in 3 other leases I'd signed. Worth it.",
        "sentiment": "positive",
        "likes": 145, "comments": 26,
        "slug": "crosby_cam_charges_lease_negotiation",
    },
    {
        "sub": "LawSchool",
        "author": "u/0L_anxious",
        "text": "Is it worth learning to draft contracts manually anymore if Crosby and similar tools are going to do it in 18 months? Asking honestly. Trying to figure out what skills to invest in.",
        "sentiment": "question",
        "likes": 98, "comments": 203,
        "slug": "should_0L_still_learn_drafting_crosby",
    },
    {
        "sub": "legaltech",
        "author": "u/clm_consultant",
        "text": "Crosby's API surface is shockingly small for an 'enterprise' product. Three endpoints. No webhooks for state changes. Hard to embed in our existing CLM workflow.",
        "sentiment": "negative",
        "likes": 67, "comments": 31,
        "slug": "crosby_api_surface_too_small",
    },
    {
        "sub": "Lawyertalk",
        "author": "u/family_law_solo",
        "text": "Tried Crosby on a contentious divorce settlement. Got a draft that was technically competent but emotionally tone-deaf in ways that would have inflamed my client. Still need humans for this.",
        "sentiment": "negative",
        "likes": 178, "comments": 84,
        "slug": "crosby_family_law_tone_deaf_draft",
    },
    {
        "sub": "biglaw",
        "author": "u/m_and_a_senior_assoc",
        "text": "Two-week diligence sprint just wrapped. Crosby chewed through ~1900 contracts and the exception report it generated was, no exaggeration, better than what our paralegals produced last cycle.",
        "sentiment": "positive",
        "likes": 503, "comments": 71,
        "slug": "crosby_1900_contract_diligence_sprint",
    },
    {
        "sub": "Entrepreneur",
        "author": "u/bootstrapper_tx",
        "text": "Bootstrapping. Cannot afford Crosby's enterprise tier. The self-serve plan is too crippled to be useful. Wish they had a real prosumer tier between the two.",
        "sentiment": "negative",
        "likes": 211, "comments": 58,
        "slug": "crosby_missing_prosumer_tier",
    },
    {
        "sub": "ChatGPTPro",
        "author": "u/ai_safety_curious",
        "text": "Crosby's CEO did a podcast on their eval methodology. They're running adversarial citation checks on every output before it leaves the model. That's the bar everyone else needs to hit.",
        "sentiment": "positive",
        "likes": 342, "comments": 96,
        "slug": "crosby_adversarial_citation_evals",
    },
    {
        "sub": "Lawyertalk",
        "author": "u/employment_law_sf",
        "text": "Crosby's California employment law coverage is shockingly current. Picked up the new noncompete rules within a week of the bill being signed. Other tools were still on old precedent for a month.",
        "sentiment": "positive",
        "likes": 269, "comments": 44,
        "slug": "crosby_ca_employment_law_fresh",
    },
    {
        "sub": "legaltech",
        "author": "u/hubspot_for_law",
        "text": "Hot take: Crosby is going to eat Clio and PracticePanther's lunch in the SMB segment within 24 months. They already have better contract workflow than either.",
        "sentiment": "neutral",
        "likes": 88, "comments": 73,
        "slug": "crosby_eating_clio_smb_segment",
    },
    {
        "sub": "startups",
        "author": "u/legal_curious_pm",
        "text": "What's Crosby's moat? Genuinely curious. The fine-tuned weights aren't defensible long-term — Anthropic or OpenAI could replicate in a quarter. Distribution into law firms, maybe?",
        "sentiment": "question",
        "likes": 124, "comments": 167,
        "slug": "crosby_moat_question_distribution",
    },
    {
        "sub": "Lawyertalk",
        "author": "u/im_law_journalist",
        "text": "Writing a piece on the new wave of AI-first law firms (Crosby et al.). DMs open if anyone has used them on a real matter and wants to chat — happy to keep it off the record.",
        "sentiment": "neutral",
        "likes": 41, "comments": 12,
        "slug": "journalist_seeking_crosby_users",
    },
    {
        "sub": "biglaw",
        "author": "u/k_street_partner",
        "text": "Our firm tested Crosby against our own associates on a regulatory comment letter. Crosby's draft was structurally tighter but missed three jurisdiction-specific edge cases. Useful, not autonomous.",
        "sentiment": "neutral",
        "likes": 197, "comments": 53,
        "slug": "crosby_vs_associates_reg_comment",
    },
    {
        "sub": "legaltech",
        "author": "u/cto_at_alsp",
        "text": "Integrated Crosby into our ALSP's intake workflow. Cut our triage-to-engagement time from 6 days to 9 hours. The classification accuracy on incoming matters is what made it work.",
        "sentiment": "positive",
        "likes": 158, "comments": 28,
        "slug": "crosby_alsp_intake_integration",
    },
    {
        "sub": "Lawyertalk",
        "author": "u/state_court_litigator",
        "text": "Crosby is built for federal practice. State court rules vary too much for it to be reliable, and it doesn't tell you when it's outside its competence zone. That's the dangerous failure mode.",
        "sentiment": "negative",
        "likes": 221, "comments": 89,
        "slug": "crosby_state_court_blind_spot",
    },
    {
        "sub": "Entrepreneur",
        "author": "u/founder_friendly_atty",
        "text": "I tell every founder client: get Crosby for first-pass on every doc, then have a human attorney review what it flags. The economics only work that way.",
        "sentiment": "positive",
        "likes": 372, "comments": 64,
        "slug": "crosby_first_pass_then_human",
    },
    {
        "sub": "ChatGPTPro",
        "author": "u/llm_observer",
        "text": "Crosby's latency on long documents is rough. 200-page credit agreement took ~4 minutes for the first pass. Competitors are sub-2 minutes. Their accuracy is better, but ops teams notice the lag.",
        "sentiment": "negative",
        "likes": 113, "comments": 37,
        "slug": "crosby_latency_long_documents",
    },
]


def _ext_id(slug: str) -> str:
    """Mimic Reddit's base36 7-char post IDs deterministically from the slug."""
    base36 = "0123456789abcdefghijklmnopqrstuvwxyz"
    h = abs(hash(slug)) % (36 ** 7)
    out = ""
    for _ in range(7):
        out = base36[h % 36] + out
        h //= 36
    return f"t3_{out}"


def _permalink(sub: str, slug: str, ext_id: str) -> str:
    short = ext_id.removeprefix("t3_")
    return f"https://www.reddit.com/r/{sub}/comments/{short}/{slug}/"


def _stagger(i: int, total: int, now: datetime) -> tuple[datetime, datetime]:
    """Return (posted_at, ingested_at) so first ~4 feel 'just landed' and the
    tail ranges back several days."""
    if i < 4:
        # 15s, 45s, 75s, 105s ago — within one 30s poll cycle of feeling fresh
        delta = timedelta(seconds=15 + i * 30 + random.randint(0, 10))
    elif i < 10:
        delta = timedelta(minutes=random.randint(8, 55))
    elif i < 18:
        delta = timedelta(hours=random.randint(2, 11))
    else:
        delta = timedelta(hours=random.randint(14, 96))
    ingested_at = now - delta
    # posted_at is 30-180s before ingestion (adapter pickup latency)
    posted_at = ingested_at - timedelta(seconds=random.randint(30, 180))
    return posted_at, ingested_at


async def main() -> dict:
    if not BRAND_ID:
        raise SystemExit("NEXT_PUBLIC_DEMO_BRAND_ID not set in .env")

    host = os.environ["CLICKHOUSE_HOST"]
    user = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD", "")

    client = clickhouse_connect.get_client(
        host=host, port=8443, username=user, password=password, secure=True,
    )

    now = datetime.now(timezone.utc)
    random.seed(20260523)  # deterministic stagger across reruns

    rows = []
    for i, p in enumerate(POSTS):
        ext_id = _ext_id(p["slug"])
        posted_at, ingested_at = _stagger(i, len(POSTS), now)
        rows.append([
            uuid.uuid4(),                          # id
            uuid.UUID(BRAND_ID),                   # brand_id
            "reddit",                              # platform
            ext_id,                                # platform_post_id
            p["author"],                           # author_handle
            random.randint(800, 64000),            # author_follower_count (karma)
            p["text"],                             # text
            [],                                    # media_urls
            p["likes"],                            # likes
            random.randint(0, max(1, p["likes"] // 30)),  # shares (xposts)
            p["comments"],                         # comments
            _permalink(p["sub"], p["slug"], ext_id),
            posted_at,                             # posted_at
            ingested_at,                           # ingested_at
            p["sentiment"],                        # sentiment
            None,                                  # cluster_id
            "nimble",                              # source
        ])

    client.insert(
        "posts",
        rows,
        column_names=[
            "id", "brand_id", "platform", "platform_post_id", "author_handle",
            "author_follower_count", "text", "media_urls", "likes", "shares",
            "comments", "permalink", "posted_at", "ingested_at", "sentiment",
            "cluster_id", "source",
        ],
    )
    client.command("OPTIMIZE TABLE posts FINAL")
    total = client.query(
        "SELECT count() FROM posts FINAL WHERE brand_id = %(b)s AND platform = 'reddit'",
        parameters={"b": BRAND_ID},
    ).result_rows[0][0]
    return {"inserted": len(rows), "total_reddit_for_brand": total}


if __name__ == "__main__":
    print(asyncio.run(main()))
