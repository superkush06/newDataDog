"""Stage 1: persist a post into ClickHouse + classify sentiment + trigger cluster."""
import uuid
from datetime import datetime, timezone

from app.core.ch import ch
from app.core.db import pool
from app.core.queue import enqueue
from app.core.realtime import publish
from app.core.metrics import statsd, span
from app.core.llm import classify_sentiment
from app.models import Post

POSTS_COLUMNS = [
    "id", "brand_id", "platform", "platform_post_id", "author_handle",
    "author_follower_count", "text", "media_urls", "likes", "shares",
    "comments", "permalink", "posted_at", "ingested_at", "sentiment",
    "cluster_id", "source",
]


@span("monitor.persist")
async def persist_post(brand_id: str, post: Post) -> str:
    """Insert into ClickHouse, classify, fan out. Returns the new post id."""
    post.sentiment = await classify_sentiment(post.text)
    post_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await ch().insert(
        "posts",
        [[
            post_id, brand_id, post.platform, post.platform_post_id,
            post.author_handle, post.author_follower_count, post.text,
            post.media_urls, post.likes, post.shares, post.comments,
            post.permalink, post.posted_at, now, post.sentiment, None,
            post.source,
        ]],
        column_names=POSTS_COLUMNS,
    )
    statsd.increment(
        "pulse.posts.ingested",
        tags=[f"platform:{post.platform}", f"source:{post.source}",
              f"sentiment:{post.sentiment}"],
    )
    await publish(brand_id, {
        "type": "new_post",
        "payload": {**post.model_dump(mode="json"), "id": post_id, "ingested_at": now.isoformat()},
    })
    await _register_for_clustering(brand_id, post_id)
    return post_id


async def _register_for_clustering(brand_id: str, post_id: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO post_vectors (post_id, brand_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
            uuid.UUID(post_id), uuid.UUID(brand_id),
        )
        unclustered = await conn.fetchval(
            "SELECT count(*) FROM post_vectors WHERE brand_id=$1 AND cluster_id IS NULL",
            uuid.UUID(brand_id),
        )
    if unclustered >= 50:
        await enqueue("cluster_run", {"brand_id": brand_id})
