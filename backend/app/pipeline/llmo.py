"""Stage L: LLM Probe — run synthetic prompts across 4 simulated LLMs.

Implementation note: all 4 LLMs are simulated via Groq with model-specific
system prompts. The judge pass that extracts mention/position/drift uses
the same Groq client (llama-3.1-8b-instant). Real provider APIs (Anthropic,
OpenAI, Perplexity) are a post-MVP swap — same probe shape.
"""
import json
import uuid
from datetime import datetime, timezone

from app.core.ch import ch
from app.core.db import pool
from app.core.queue import enqueue
from app.core.metrics import statsd, span
from app.core.llm import _get_client, JUDGE_MODEL

LLMS = ["claude", "chatgpt", "gemini", "perplexity"]
REPETITIONS = 3  # within-prompt repetition for stability (research: ≥2 → 88.9% acc)

SYSTEM_PROMPTS = {
    "claude": "You are Claude, Anthropic's helpful AI assistant. Respond with measured analysis, multiple perspectives, and structured reasoning. Training cutoff late 2024.",
    "chatgpt": "You are ChatGPT by OpenAI. Respond in a conversational, list-heavy style. Training cutoff Oct 2023. Favor mainstream sources.",
    "gemini": "You are Google Gemini. Respond authoritatively with citations and current info up to early 2025.",
    "perplexity": "You are Perplexity AI. Respond with cited answers and ranked recommendations. Heavy on numerical comparisons.",
}

# Use a Groq model that handles long generations well; same as drafts.
IMPERSONATION_MODEL = "llama-3.3-70b-versatile"


def position_weight(pos: int) -> float:
    return {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.2}.get(pos, 0.0)


async def _run_one(llm: str, prompt: str, brand_name: str,
                   competitors: list[str], ground_truth: str) -> dict:
    client = _get_client()

    # Step 1: simulate the target LLM's response
    sys = SYSTEM_PROMPTS[llm]
    resp = await client.chat.completions.create(
        model=IMPERSONATION_MODEL,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    text = (resp.choices[0].message.content or "").strip()

    # Step 2: judge it against the ground truth (structured JSON)
    judge = await client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{
            "role": "user",
            "content": (
                "Analyze this LLM response for brand mentions.\n"
                f"BRAND: {brand_name}\n"
                f"COMPETITORS: {', '.join(competitors) or '(none)'}\n"
                f"GROUND TRUTH ABOUT BRAND: {ground_truth[:1500]}\n"
                f"RESPONSE:\n{text}\n\n"
                "Return JSON with exactly these keys: "
                "{mentioned: bool, position: 0-4 (0 absent, 1 headline, 2 early, 3 late, 4 list-item), "
                "competitors_mentioned: [...], sentiment: -1.0 to 1.0, "
                "claims: [factual claims about the brand], "
                "drift_score: 0.0 to 1.0 (factual departure from ground truth, 0 if not mentioned)}"
            ),
        }],
        response_format={"type": "json_object"},
        max_tokens=400,
    )
    try:
        d = json.loads(judge.choices[0].message.content or "{}")
    except Exception:
        d = {}

    return {
        "llm": llm, "prompt": prompt, "response": text,
        "mentioned": bool(d.get("mentioned", False)),
        "position": int(d.get("position", 0) or 0),
        "competitors_mentioned": d.get("competitors_mentioned", []) or [],
        "sentiment": float(d.get("sentiment", 0.0) or 0.0),
        "claims": d.get("claims", []) or [],
        "drift_score": float(d.get("drift_score", 0.0) or 0.0),
    }


@span("llmo.probe")
async def run_probe(brand_id: str):
    """One full LLM probe iteration for a brand: all prompts × all LLMs × REPETITIONS."""
    bid = uuid.UUID(brand_id)
    async with pool.acquire() as conn:
        brand = await conn.fetchrow(
            "SELECT name, ground_truth, competitors FROM brands WHERE id=$1", bid,
        )
        prompts = await conn.fetch(
            "SELECT id, prompt FROM brand_prompts WHERE brand_id=$1 LIMIT 20", bid,
        )
    if not brand or not prompts:
        return

    competitors = list(brand["competitors"] or [])
    ground_truth = brand["ground_truth"] or ""
    rows_to_insert = []

    for prow in prompts:
        for llm in LLMS:
            for _ in range(REPETITIONS):
                r = await _run_one(llm, prow["prompt"], brand["name"], competitors, ground_truth)
                citation_accuracy = 100.0 * (1.0 - r["drift_score"]) if r["mentioned"] else 0.0
                rows_to_insert.append([
                    str(uuid.uuid4()), brand_id, llm,
                    r["prompt"], str(prow["id"]), r["response"],
                    1 if r["mentioned"] else 0,
                    r["position"], r["competitors_mentioned"],
                    r["sentiment"], r["claims"],
                    r["drift_score"], citation_accuracy,
                    datetime.now(timezone.utc),
                ])
                statsd.increment(
                    "pulse.llmo.probe",
                    tags=[f"llm:{llm}", f"mentioned:{int(r['mentioned'])}", f"brand:{brand_id}"],
                )

    if rows_to_insert:
        await ch().insert(
            "llmo_audits", rows_to_insert,
            column_names=[
                "id", "brand_id", "llm", "prompt", "prompt_id", "response",
                "mentioned", "position", "competitors_mentioned", "sentiment",
                "claims", "drift_score", "citation_accuracy", "ingested_at",
            ],
        )

    # Drift > 0.4 on any audit fires a ground_truth_correction action
    high_drift = [r for r in rows_to_insert if r[11] > 0.4]
    if high_drift:
        await enqueue("draft_correction", {
            "brand_id": brand_id,
            "audit_ids": [r[0] for r in high_drift[:3]],
        })

    await enqueue("score_recompute", {"brand_id": brand_id})
