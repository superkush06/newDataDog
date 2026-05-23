CREATE TABLE IF NOT EXISTS llmo_audits (
    id                    UUID,
    brand_id              UUID,
    prompt_id             Nullable(UUID),
    provider              LowCardinality(String),
    model                 LowCardinality(String),
    prompt                String,
    response              String,
    cited                 UInt8,
    mention_rank          UInt8,
    visibility_score      Float32,
    sentiment_score       Float32,
    citations             Array(String),
    claims                Array(String),
    drift_score           Float32,
    raw                   String,
    created_at            DateTime64(3, 'UTC') DEFAULT now64()
)
ENGINE = MergeTree
ORDER BY (brand_id, provider, model, created_at);
