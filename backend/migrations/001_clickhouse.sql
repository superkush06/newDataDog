CREATE TABLE IF NOT EXISTS posts (
    id                    UUID,
    brand_id              UUID,
    platform              LowCardinality(String),
    platform_post_id      String,
    author_handle         String,
    author_follower_count UInt32,
    text                  String,
    media_urls            Array(String),
    likes                 UInt32,
    shares                UInt32,
    comments              UInt32,
    permalink             String,
    posted_at             DateTime64(3, 'UTC'),
    ingested_at           DateTime64(3, 'UTC') DEFAULT now64(),
    sentiment             LowCardinality(String),
    cluster_id            Nullable(UUID),
    source                LowCardinality(String)
)
ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (brand_id, platform, platform_post_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS cluster_engagement_mv
ENGINE = SummingMergeTree
ORDER BY (brand_id, cluster_id)
AS SELECT
    brand_id, cluster_id,
    count()                       AS post_count,
    sum(likes)                    AS likes,
    sum(shares)                   AS shares,
    sum(comments)                 AS comments,
    max(author_follower_count)    AS max_followers,
    countIf(sentiment = 'negative') AS neg_count
FROM posts
WHERE cluster_id IS NOT NULL
GROUP BY brand_id, cluster_id;
