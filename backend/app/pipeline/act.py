"""Stage 4: choose action type, draft via Gemini, persist as pending action."""
import json
import uuid
from app.core.db import pool
from app.core.ch import ch
from app.core.llm import classify_action_type, draft_response
from app.core.realtime import publish
from app.core.metrics import span
from app.config import CHAR_LIMITS


@span("act.run")
async def run_act(cluster_id: str):
    cid = uuid.UUID(cluster_id)
    async with pool.acquire() as conn:
        cluster = await conn.fetchrow("SELECT * FROM clusters WHERE id=$1", cid)
        if not cluster:
            return
        brand = await conn.fetchrow(
            "SELECT id, name, vertical, voice_guidelines, connections, thresholds "
            "FROM brands WHERE id=$1", cluster["brand_id"],
        )

    top_rows = (await ch().query(
        """
        SELECT id, platform, text, likes, shares, comments, permalink, sentiment
        FROM posts WHERE cluster_id = %(cid)s
        ORDER BY (likes + shares*5 + comments*3) DESC LIMIT 20
        """,
        {"cid": cluster_id},
    )).result_rows

    cluster_d = dict(cluster)
    cluster_d["thresholds"] = brand["thresholds"]
    action_type = await classify_action_type(cluster_d, top_rows)

    draft = await _generate(action_type, dict(brand), cluster_d, top_rows)

    # Healthcare brands route ticket actions to Luminai when destination layer is wired.
    if action_type == "ticket" and brand["vertical"] == "healthcare":
        draft["destination"] = "luminai"

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO actions (brand_id, type, state, cluster_id,
                target_post_id, draft, context)
            VALUES ($1,$2,'pending',$3,$4,$5::jsonb,$6::jsonb) RETURNING id
            """,
            brand["id"], action_type, cid, draft.get("target_post_id"),
            json.dumps(draft),
            json.dumps({
                "cluster_summary": cluster["summary"],
                "similar_report_count": cluster["post_count"],
            }),
        )

    await publish(str(brand["id"]), {
        "type": "action_created",
        "payload": {"id": str(row["id"]), "type": action_type},
    })


async def _generate(action_type: str, brand: dict, cluster: dict, posts: list) -> dict:
    if action_type == "response" and posts:
        top = posts[0]
        platform = top[1]
        limit = CHAR_LIMITS[platform]
        text = await draft_response(brand, cluster, top[2], limit)
        return {
            "text": text, "char_count": len(text), "char_limit": limit,
            "platform": platform, "target_post_id": str(top[0]),
        }
    if action_type == "ticket":
        return {
            "title": cluster["name"],
            "description": cluster["summary"],
            "priority": f"P1 (score: {cluster['severity_score']:.0f})",
            "social_links": [p[6] for p in posts[:5]],
        }
    if action_type == "escalation":
        return {
            "channel": brand.get("connections", {}).get("slack", ""),
            "summary": cluster["summary"],
            "top_posts": [p[6] for p in posts[:5]],
            "recommended_actions": ["Acknowledge publicly", "Open war room"],
        }
    return {"note": f"action type {action_type} draft pending"}


async def run_correction(brand_id: str, audit_ids: list[str]):
    """Generate a ground_truth_correction draft from drifted LLMO audits."""
    from app.core.llm import _get_client
    from google.genai import types as _types

    async with pool.acquire() as conn:
        brand = await conn.fetchrow(
            "SELECT id, name, ground_truth FROM brands WHERE id=$1", uuid.UUID(brand_id)
        )
    audits = (await ch().query(
        "SELECT llm, prompt, response, claims, drift_score "
        "FROM llmo_audits WHERE id IN %(ids)s",
        {"ids": audit_ids},
    )).result_rows
    if not audits:
        return

    client = _get_client()
    sample = "\n\n".join([f"[{a[0]}] {a[2][:400]}" for a in audits])
    prompt = (
        f"You are correcting public AI descriptions of {brand['name']}.\n\n"
        f"GROUND TRUTH:\n{brand['ground_truth']}\n\n"
        f"DRIFTED LLM RESPONSES:\n{sample}\n\n"
        "Draft a single 2-3 sentence correction statement Pulse can publish "
        "(LinkedIn post, AI feedback form, brand-page update). Focus on the "
        "specific inaccuracies. Be calm and factual."
    )
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-pro", contents=prompt,
        config=_types.GenerateContentConfig(max_output_tokens=400),
    )
    text = (resp.text or "").strip()

    async with pool.acquire() as conn:
        cluster_id = await conn.fetchval(
            "SELECT id FROM clusters WHERE brand_id=$1 AND status='active' "
            "ORDER BY last_activity_at DESC NULLS LAST LIMIT 1", uuid.UUID(brand_id),
        )
        if not cluster_id:
            cluster_id = await conn.fetchval(
                """
                INSERT INTO clusters (brand_id, name, summary, severity, severity_score)
                VALUES ($1, 'LLM Ground Truth Drift', $2, 'high', 600) RETURNING id
                """, uuid.UUID(brand_id),
                f"Detected drift in {len(audits)} LLM responses.",
            )

        await conn.execute(
            """
            INSERT INTO actions (brand_id, type, state, cluster_id, draft, context)
            VALUES ($1,'ground_truth_correction','pending',$2,$3::jsonb,$4::jsonb)
            """,
            uuid.UUID(brand_id), cluster_id,
            json.dumps({"text": text, "destinations": ["linkedin", "brand_page"],
                        "drifted_llms": list({a[0] for a in audits})}),
            json.dumps({"cluster_summary": "LLM drift detected",
                        "similar_report_count": len(audits)}),
        )
