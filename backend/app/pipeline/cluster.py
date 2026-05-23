"""Stage 2: embed unclustered posts, assign to nearest cluster or create new."""
import uuid
from app.core.db import pool
from app.core.ch import ch
from app.core.llm import embed_batch, summarize_cluster
from app.core.queue import enqueue
from app.core.metrics import span
from app.config import settings


@span("cluster.run")
async def run_clustering(brand_id: str):
    bid = uuid.UUID(brand_id)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT post_id FROM post_vectors WHERE brand_id=$1 AND cluster_id IS NULL LIMIT 100",
            bid,
        )
        if not rows:
            return
        ids = [r["post_id"] for r in rows]
        id_strs = [str(i) for i in ids]

        ch_rows = await ch().query(
            "SELECT id, text FROM posts WHERE id IN %(ids)s",
            {"ids": id_strs},
        )
        text_by_id = {str(r[0]): r[1] for r in ch_rows.result_rows}
        texts = [text_by_id.get(s, "") for s in id_strs]

        vectors = await embed_batch(texts)

        for post_id, vec in zip(ids, vectors):
            await conn.execute(
                "UPDATE post_vectors SET embedding=$1 WHERE post_id=$2",
                vec, post_id,
            )
            match = await conn.fetchrow(
                """
                SELECT cluster_id, 1 - (embedding <=> $1) AS sim
                FROM post_vectors
                WHERE brand_id=$2 AND cluster_id IS NOT NULL AND embedding IS NOT NULL
                ORDER BY embedding <=> $1 LIMIT 1
                """,
                vec, bid,
            )
            if match and match["sim"] is not None and match["sim"] > settings.cluster_similarity_threshold:
                cid = match["cluster_id"]
            else:
                cid = await _create_cluster(conn, bid, text_by_id.get(str(post_id), ""))

            await conn.execute(
                "UPDATE post_vectors SET cluster_id=$1 WHERE post_id=$2",
                cid, post_id,
            )
            await ch().command(
                "ALTER TABLE posts UPDATE cluster_id=%(c)s WHERE id=%(p)s",
                {"c": str(cid), "p": str(post_id)},
            )

        await _merge_similar_clusters(conn, bid)

    await enqueue("score_run", {"brand_id": brand_id})


async def _create_cluster(conn, brand_id: uuid.UUID, founding_text: str) -> uuid.UUID:
    name, summary, tags = await summarize_cluster([founding_text])
    row = await conn.fetchrow(
        """
        INSERT INTO clusters (brand_id, name, summary, tags, post_count,
            first_seen_at, last_activity_at)
        VALUES ($1,$2,$3,$4,1, now(), now()) RETURNING id
        """,
        brand_id, name, summary, tags,
    )
    return row["id"]


async def _merge_similar_clusters(conn, brand_id: uuid.UUID):
    pairs = await conn.fetch(
        """
        SELECT a.id AS keep, b.id AS drop
        FROM clusters a JOIN clusters b
          ON a.brand_id=b.brand_id AND a.id < b.id
        WHERE a.brand_id=$1
          AND a.centroid IS NOT NULL AND b.centroid IS NOT NULL
          AND 1 - (a.centroid <=> b.centroid) > $2
        """,
        brand_id, settings.merge_similarity_threshold,
    )
    for p in pairs:
        await conn.execute(
            "UPDATE post_vectors SET cluster_id=$1 WHERE cluster_id=$2",
            p["keep"], p["drop"],
        )
        await ch().command(
            "ALTER TABLE posts UPDATE cluster_id=%(k)s WHERE cluster_id=%(d)s",
            {"k": str(p["keep"]), "d": str(p["drop"])},
        )
        await conn.execute("DELETE FROM clusters WHERE id=$1", p["drop"])
