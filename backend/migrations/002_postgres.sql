CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS brands (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  vertical        TEXT NOT NULL DEFAULT 'generic',
  voice_guidelines TEXT,
  keywords        TEXT[] NOT NULL DEFAULT '{}',
  thresholds      JSONB NOT NULL DEFAULT '{"critical":700,"high":400,"medium":200}',
  connections     JSONB NOT NULL DEFAULT '{}',
  nimble_cursor   TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

DO $$ BEGIN
  CREATE TYPE severity_enum AS ENUM ('critical','high','medium','low');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE cluster_status_enum AS ENUM ('active','resolved','snoozed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS clusters (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id            UUID NOT NULL REFERENCES brands(id),
  name                TEXT,
  summary             TEXT,
  centroid            VECTOR(768),
  post_count          INT NOT NULL DEFAULT 0,
  severity            severity_enum NOT NULL DEFAULT 'low',
  severity_score      FLOAT NOT NULL DEFAULT 0,
  tags                TEXT[] NOT NULL DEFAULT '{}',
  sentiment_breakdown JSONB NOT NULL DEFAULT '{}',
  platforms           TEXT[] NOT NULL DEFAULT '{}',
  first_seen_at       TIMESTAMPTZ,
  last_activity_at    TIMESTAMPTZ,
  status              cluster_status_enum NOT NULL DEFAULT 'active',
  pinned_severity     severity_enum
);

CREATE TABLE IF NOT EXISTS post_vectors (
  post_id    UUID PRIMARY KEY,
  brand_id   UUID NOT NULL REFERENCES brands(id),
  embedding  VECTOR(768),
  cluster_id UUID REFERENCES clusters(id)
);

CREATE INDEX IF NOT EXISTS post_vectors_embedding_idx
  ON post_vectors USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS post_vectors_unclustered_idx
  ON post_vectors (brand_id) WHERE cluster_id IS NULL;

DO $$ BEGIN
  CREATE TYPE action_type_enum AS ENUM ('response','ticket','escalation','faq','insight','dm');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE action_state_enum AS ENUM ('pending','approved','executed','rejected');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS actions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id       UUID NOT NULL REFERENCES brands(id),
  type           action_type_enum NOT NULL,
  state          action_state_enum NOT NULL DEFAULT 'pending',
  cluster_id     UUID NOT NULL REFERENCES clusters(id),
  target_post_id UUID,
  draft          JSONB NOT NULL,
  context        JSONB NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at     TIMESTAMPTZ,
  decided_by     UUID,
  reject_reason  TEXT,
  outcome        JSONB
);

CREATE INDEX IF NOT EXISTS actions_pending_idx
  ON actions (brand_id, created_at) WHERE state = 'pending';
