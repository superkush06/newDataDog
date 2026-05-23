"""Stage 3: read ClickHouse aggregates, compute severity, write back to Postgres."""
import uuid
from app.core.db import pool
from app.core.ch import ch
from app.core.queue import enqueue
from app.core.metrics import statsd, span
from app.pipeline.score_formula import compute_score, severity_label


@span("score.run")
async def run_scoring(brand_id: str):
    bid = uuid.UUID(brand_id)
    async with pool.acquire() as conn:
        thresholds = await conn.fetchval(
            "SELECT thresholds FROM brands WHERE id=$1", bid,
        )
        clusters = await conn.fetch(
            "SELECT id FROM clusters WHERE brand_id=$1 AND status='active'", bid,
        )

        for c in clusters:
            cid = c["id"]
            agg = await ch().query(
                """
                SELECT
                  any(post_count), any(likes), any(shares), any(comments),
                  any(max_followers), any(neg_count),
                  (SELECT count() FROM posts
                     WHERE cluster_id = %(cid)s
                       AND posted_at > now() - INTERVAL 2 HOUR) AS recent
                FROM cluster_engagement_mv
                WHERE cluster_id = %(cid)s
                """,
                {"cid": str(cid)},
            )
            if not agg.result_rows:
                continue
            n, likes, shares, comments, max_followers, neg, recent = agg.result_rows[0]
            score_d = compute_score(
                post_count=int(n or 0), likes=int(likes or 0),
                shares=int(shares or 0), comments=int(comments or 0),
                max_followers=int(max_followers or 0), neg_count=int(neg or 0),
                recent_2h=int(recent or 0),
            )
            label = severity_label(score_d["severity_score"], thresholds)

            await conn.execute(
                """
                UPDATE clusters
                SET severity_score=$1, severity=$2, post_count=$3,
                    last_activity_at = greatest(last_activity_at, now())
                WHERE id=$4
                """,
                score_d["severity_score"], label, int(n or 0), cid,
            )
            statsd.gauge(
                "pulse.cluster.severity_score",
                score_d["severity_score"],
                tags=[f"severity:{label}", f"brand:{brand_id}"],
            )
            if label == "critical":
                await enqueue("act_run", {"cluster_id": str(cid)})
