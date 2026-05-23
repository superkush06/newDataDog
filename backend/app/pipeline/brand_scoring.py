"""Brand-level rollup: SocialScore + LLMOScore + Overall."""
import json
import uuid
from app.core.db import pool
from app.core.ch import ch
from app.core.metrics import statsd, span
from app.pipeline.llmo_scoring import (
    citation_frequency, share_of_voice, citation_accuracy,
    sentiment_quality, compute_llmo_score,
)

LLMS = ["claude", "chatgpt", "gemini", "perplexity"]


def drift_label(citation_acc: float) -> str:
    if citation_acc >= 80:
        return "low"
    if citation_acc >= 50:
        return "medium"
    return "high"


@span("brand_scoring.recompute")
async def recompute(brand_id: str) -> dict:
    bid = uuid.UUID(brand_id)

    # SocialScore from active cluster severity counts in last 24h
    async with pool.acquire() as conn:
        sev_rows = await conn.fetch(
            """
            SELECT severity, count(*) AS n FROM clusters
            WHERE brand_id=$1 AND status='active'
              AND last_activity_at > now() - INTERVAL '24 hours'
            GROUP BY severity
            """, bid,
        )
    sev_counts = {r["severity"]: r["n"] for r in sev_rows}
    pressure = (sev_counts.get("critical", 0) * 30
                + sev_counts.get("high", 0) * 15
                + sev_counts.get("medium", 0) * 5)
    social = max(0.0, min(100.0, 100.0 - pressure))

    # LLMOScore from llmo_audits in last 24h
    audits_rows = (await ch().query(
        """
        SELECT llm, mentioned, position, competitors_mentioned,
               sentiment, drift_score
        FROM llmo_audits
        WHERE brand_id = %(b)s AND ingested_at > now() - INTERVAL 24 HOUR
        """,
        {"b": brand_id},
    )).result_rows

    audits = [{
        "llm": r[0], "mentioned": bool(r[1]), "position": int(r[2]),
        "competitors_mentioned": list(r[3] or []),
        "sentiment": float(r[4]), "drift_score": float(r[5]),
    } for r in audits_rows]

    cf = citation_frequency(audits)
    sov = share_of_voice(audits)
    ca = citation_accuracy(audits)
    sq = sentiment_quality(audits)
    llmo = compute_llmo_score(cf, sov, ca, sq)

    per_llm = {}
    for llm in LLMS:
        ll_audits = [a for a in audits if a["llm"] == llm]
        if not ll_audits:
            per_llm[llm] = {"score": 0.0, "mention_rate": 0.0,
                            "avg_position": 0.0, "drift": "high"}
            continue
        mr = sum(1 for a in ll_audits if a["mentioned"]) / len(ll_audits) * 100
        positions = [a["position"] for a in ll_audits if a["mentioned"]]
        avg_pos = sum(positions) / len(positions) if positions else 0
        l_ca = citation_accuracy(ll_audits)
        l_score = compute_llmo_score(
            citation_frequency(ll_audits), share_of_voice(ll_audits),
            l_ca, sentiment_quality(ll_audits),
        )
        per_llm[llm] = {"score": l_score, "mention_rate": round(mr, 1),
                        "avg_position": round(avg_pos, 2),
                        "drift": drift_label(l_ca)}

    overall = round(0.5 * social + 0.5 * llmo, 2)

    breakdown = {
        "social_breakdown": {
            "critical_clusters": sev_counts.get("critical", 0),
            "high_clusters": sev_counts.get("high", 0),
            "medium_clusters": sev_counts.get("medium", 0),
        },
        "llmo_breakdown": {
            "citation_frequency": round(cf, 2),
            "share_of_voice": round(sov, 2),
            "citation_accuracy": round(ca, 2),
            "sentiment_quality": round(sq, 2),
            "per_llm": per_llm,
        },
    }

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO pulse_scores (brand_id, overall, social, llmo, breakdown) "
            "VALUES ($1,$2,$3,$4,$5::jsonb)",
            bid, overall, social, llmo, json.dumps(breakdown),
        )

    statsd.gauge("pulse.brand.overall", overall, tags=[f"brand:{brand_id}"])
    statsd.gauge("pulse.brand.social", social, tags=[f"brand:{brand_id}"])
    statsd.gauge("pulse.brand.llmo", llmo, tags=[f"brand:{brand_id}"])

    return {"overall": overall, "social": social, "llmo": llmo, **breakdown}
