DROP TABLE IF EXISTS llmo_audits;

CREATE TABLE llmo_audits (
    id                    UUID,
    brand_id              UUID,
    llm                   LowCardinality(String),
    prompt                String,
    prompt_id             Nullable(String),
    response              String,
    mentioned             UInt8,
    position              UInt8,
    competitors_mentioned Array(String),
    sentiment             Float32,
    claims                Array(String),
    drift_score           Float32,
    citation_accuracy     Float32,
    ingested_at           DateTime64(3, 'UTC') DEFAULT now64()
)
ENGINE = MergeTree
ORDER BY (brand_id, llm, ingested_at);
