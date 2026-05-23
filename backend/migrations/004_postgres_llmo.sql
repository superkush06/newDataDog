ALTER TABLE brands ADD COLUMN IF NOT EXISTS ground_truth TEXT;
ALTER TABLE brands ADD COLUMN IF NOT EXISTS competitors TEXT[] NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS brand_prompts (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id   UUID NOT NULL REFERENCES brands(id),
    prompt     TEXT NOT NULL,
    intent     TEXT NOT NULL DEFAULT 'discovery',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS brand_prompts_brand_idx
    ON brand_prompts (brand_id, created_at DESC);

CREATE TABLE IF NOT EXISTS pulse_scores (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id   UUID NOT NULL REFERENCES brands(id),
    overall    FLOAT NOT NULL,
    social     FLOAT NOT NULL,
    llmo       FLOAT NOT NULL,
    breakdown  JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS pulse_scores_brand_idx
    ON pulse_scores (brand_id, created_at DESC);
