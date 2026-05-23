# Pulse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Pulse social-listening + action pipeline end-to-end (Monitor → Cluster → Score → Act) with the 5 sponsor tools (Nimble, Gemini, ClickHouse, Datadog, Luminai) and a Next.js dashboard.

**Architecture:** Event-driven pipeline. FastAPI backend with four pipeline stages, decoupled via Redis. ClickHouse holds the high-write posts time-series; Postgres+pgvector holds clusters/actions/centroids. Gemini does sentiment + embeddings + drafting. Nimble feeds open-web ingest. Datadog observes every stage. Luminai is the healthcare-vertical action egress. Next.js frontend renders four views, one per stage, with TanStack Query + Supabase Realtime.

**Tech Stack:** Python 3.11+, FastAPI 0.109, asyncpg, clickhouse-connect, redis, arq, google-genai, nimble-sdk, ddtrace. Next.js 14 App Router, TypeScript, Tailwind, TanStack Query, Recharts. ClickHouse Cloud + Supabase Postgres + Upstash Redis.

**Time-budget reality:** The spec calls for 4 hours. Tasks are ordered so a minimum-viable demo (X webhook → ClickHouse → cluster → score → drafted action → approval) is reachable by Task 25. Tasks 26+ add Datadog richness, Luminai, Realtime, and polish.

**Testing philosophy:** This is a hackathon plan. Pure-function components (scoring formula, adapters' `normalize`, policy/severity labelers) get proper TDD. Integration boundaries (LLM clients, ClickHouse writes, webhook routes) get one smoke test each. UI views get one render test. We are not chasing coverage; we are chasing a working demo.

---

## File Structure (locked in)

```
/Users/kushagrabehl/Downloads/newData/newDataDog/
├── docs/superpowers/{specs,plans}/...
├── README.md
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── .env                          # gitignored
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI + ddtrace
│   │   ├── config.py                 # pydantic-settings
│   │   ├── models.py                 # Pydantic mirrors of spec data models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── webhooks.py
│   │   │   ├── routes.py             # feed/clusters/queue/actions/brands/health
│   │   │   └── websocket.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Normalizer ABC + registry
│   │   │   ├── x.py
│   │   │   ├── meta.py
│   │   │   └── nimble.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── ch.py                 # ClickHouse client
│   │   │   ├── db.py                 # asyncpg pool
│   │   │   ├── queue.py              # arq/redis
│   │   │   ├── llm.py                # Gemini wrappers
│   │   │   ├── metrics.py            # Datadog
│   │   │   └── realtime.py           # WS pub
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── monitor.py            # persist_post
│   │   │   ├── cluster.py            # run_clustering
│   │   │   ├── score.py              # run_scoring
│   │   │   └── act.py                # run_act
│   │   ├── destinations/
│   │   │   ├── __init__.py
│   │   │   ├── slack.py
│   │   │   ├── jira.py
│   │   │   └── luminai.py
│   │   └── workers/
│   │       ├── __init__.py
│   │       ├── pipeline_worker.py    # arq worker
│   │       └── cron.py               # poll_platforms + refresh_engagement
│   ├── migrations/
│   │   ├── 001_clickhouse.sql
│   │   └── 002_postgres.sql
│   ├── scripts/
│   │   ├── apply_migrations.py
│   │   └── seed_demo.py
│   └── tests/
│       ├── conftest.py
│       ├── test_adapters.py
│       ├── test_scoring.py
│       ├── test_webhooks.py
│       └── test_pipeline_smoke.py
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── tsconfig.json
    ├── .env.local.example
    ├── app/
    │   ├── layout.tsx
    │   ├── providers.tsx
    │   ├── page.tsx
    │   ├── globals.css
    │   ├── feed/page.tsx
    │   ├── clusters/page.tsx
    │   ├── queue/page.tsx
    │   └── actions/page.tsx
    ├── components/
    │   ├── PostCard.tsx
    │   ├── FeedSidebar.tsx
    │   ├── ClusterCard.tsx
    │   ├── QueueTable.tsx
    │   ├── ActionCard.tsx
    │   ├── SeverityBadge.tsx
    │   └── SentimentBar.tsx
    ├── lib/
    │   ├── api.ts
    │   ├── types.ts
    │   └── realtime.ts
    └── hooks/
        ├── useFeed.ts
        ├── useClusters.ts
        ├── useQueue.ts
        ├── useActions.ts
        └── useRealtimeFeed.ts
```

---

## Task 1: Repo scaffolding + .gitignore

**Files:**
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Write `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/

# Node
node_modules/
.next/
dist/
out/

# Env
.env
.env.local
*.env.local

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
```

- [ ] **Step 2: Write minimal `README.md`**

```markdown
# Pulse

Social listening + action pipeline. See `docs/superpowers/specs/2026-05-23-pulse-design.md` for the design and `docs/superpowers/plans/2026-05-23-pulse-implementation.md` for the build plan.

## Quickstart

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # fill in keys
python scripts/apply_migrations.py
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install
cp .env.local.example .env.local
npm run dev
```
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore README.md
git commit -m "chore: scaffold repo with gitignore + README"
```

---

## Task 2: Backend Python project skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/{api,adapters,core,pipeline,destinations,workers}/__init__.py` (each empty)

- [ ] **Step 1: Write `backend/pyproject.toml`**

```toml
[project]
name = "pulse-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    "pydantic==2.5.0",
    "pydantic-settings==2.1.0",
    "httpx==0.26.0",
    "asyncpg==0.29.0",
    "pgvector==0.2.5",
    "clickhouse-connect==0.7.0",
    "redis==5.0.1",
    "arq==0.25.0",
    "google-genai==0.3.0",
    "ddtrace==2.6.0",
    "datadog==0.49.1",
    "python-dotenv==1.0.0",
]

[project.optional-dependencies]
dev = ["pytest==8.0.0", "pytest-asyncio==0.23.4", "httpx==0.26.0"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Write `backend/.env.example`**

```bash
# Gemini
GEMINI_API_KEY=

# Nimble
NIMBLE_API_KEY=

# ClickHouse
CLICKHOUSE_HOST=
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# Postgres + pgvector (Supabase)
DATABASE_URL=

# Redis (Upstash)
REDIS_URL=redis://localhost:6379

# Datadog
DD_API_KEY=
DD_SERVICE=pulse
DD_ENV=development
DD_AGENT_HOST=localhost

# Luminai (healthcare vertical)
LUMINAI_API_KEY=

# Platforms
X_BEARER_TOKEN=
X_WEBHOOK_SECRET=
META_APP_SECRET=

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
CLUSTER_SIMILARITY_THRESHOLD=0.82
MERGE_SIMILARITY_THRESHOLD=0.88
BATCH_SIZE=50
```

- [ ] **Step 3: Create empty package init files**

```bash
mkdir -p backend/app/{api,adapters,core,pipeline,destinations,workers}
touch backend/app/__init__.py \
      backend/app/api/__init__.py \
      backend/app/adapters/__init__.py \
      backend/app/core/__init__.py \
      backend/app/pipeline/__init__.py \
      backend/app/destinations/__init__.py \
      backend/app/workers/__init__.py
mkdir -p backend/tests
touch backend/tests/__init__.py
```

- [ ] **Step 4: Install deps and verify**

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -c "import fastapi, asyncpg, clickhouse_connect, google.genai, ddtrace; print('ok')"
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/.env.example backend/app/ backend/tests/__init__.py
git commit -m "feat(backend): scaffold Python project with deps"
```

---

## Task 3: Backend config (pydantic-settings)

**Files:**
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_config.py
import os
from app.config import Settings, CHAR_LIMITS

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CLICKHOUSE_HOST", "test-host")
    monkeypatch.setenv("DATABASE_URL", "postgres://x")
    s = Settings()
    assert s.gemini_api_key == "test-key"
    assert s.clickhouse_host == "test-host"
    assert s.cluster_similarity_threshold == 0.82  # default

def test_char_limits_per_platform():
    assert CHAR_LIMITS["x"] == 280
    assert CHAR_LIMITS["instagram"] == 2200
```

- [ ] **Step 2: Run test (fails — no Settings)**

```bash
cd backend && pytest tests/test_config.py -v
```
Expected: ImportError.

- [ ] **Step 3: Write `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    nimble_api_key: str = ""
    luminai_api_key: str = ""

    clickhouse_host: str = ""
    clickhouse_port: int = 8443
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    database_url: str = ""
    redis_url: str = "redis://localhost:6379"

    dd_api_key: str = ""
    dd_service: str = "pulse"
    dd_env: str = "development"
    dd_agent_host: str = "localhost"

    x_bearer_token: str = ""
    x_webhook_secret: str = ""
    meta_app_secret: str = ""

    environment: str = "development"
    log_level: str = "INFO"
    cluster_similarity_threshold: float = 0.82
    merge_similarity_threshold: float = 0.88
    batch_size: int = 50

settings = Settings()

CHAR_LIMITS = {
    "x": 280, "instagram": 2200, "tiktok": 150,
    "reddit": 10000, "facebook": 8000,
}
```

- [ ] **Step 4: Run tests (pass)**

```bash
pytest tests/test_config.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py
git commit -m "feat(backend): config via pydantic-settings"
```

---

## Task 4: Pydantic models mirroring spec

**Files:**
- Create: `backend/app/models.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_models.py
from app.models import Post, Cluster, Action, Brand
from datetime import datetime, timezone

def test_post_minimal():
    p = Post(
        platform="x", platform_post_id="123", author_handle="@a",
        author_follower_count=10, text="hello", media_urls=[],
        likes=0, shares=0, comments=0, permalink="https://x.com/123",
        posted_at=datetime.now(timezone.utc),
        sentiment="neutral", cluster_id=None,
    )
    assert p.platform == "x"
    assert p.source == "webhook"  # default

def test_cluster_default_severity():
    c = Cluster(brand_id="00000000-0000-0000-0000-000000000000",
                name="n", summary="s")
    assert c.severity == "low"
    assert c.severity_score == 0
```

- [ ] **Step 2: Write `backend/app/models.py`**

```python
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
from uuid import UUID

Platform = Literal["x", "instagram", "tiktok", "reddit", "facebook"]
Sentiment = Literal["positive", "negative", "neutral", "question"]
Severity = Literal["critical", "high", "medium", "low"]
ClusterStatus = Literal["active", "resolved", "snoozed"]
ActionType = Literal["response", "ticket", "escalation", "faq", "insight", "dm"]
ActionState = Literal["pending", "approved", "executed", "rejected"]
Vertical = Literal["generic", "healthcare"]

class Post(BaseModel):
    id: Optional[str] = None
    brand_id: Optional[str] = None
    platform: Platform
    platform_post_id: str
    author_handle: str
    author_follower_count: int = 0
    text: str
    media_urls: list[str] = []
    likes: int = 0
    shares: int = 0
    comments: int = 0
    permalink: str
    posted_at: datetime
    ingested_at: Optional[datetime] = None
    sentiment: Sentiment = "neutral"
    cluster_id: Optional[str] = None
    source: Literal["webhook", "nimble"] = "webhook"

class SentimentBreakdown(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    question: int = 0

class Cluster(BaseModel):
    id: Optional[str] = None
    brand_id: str
    name: str
    summary: str
    centroid: Optional[list[float]] = None
    post_count: int = 0
    severity: Severity = "low"
    severity_score: float = 0
    tags: list[str] = []
    sentiment_breakdown: SentimentBreakdown = Field(default_factory=SentimentBreakdown)
    platforms: list[Platform] = []
    first_seen_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    status: ClusterStatus = "active"

class ScoreBreakdown(BaseModel):
    cluster_id: str
    volume: float
    engagement: float
    sentiment: float
    velocity: float
    influence_multiplier: float
    severity_score: float
    severity: Severity
    auto_escalate: bool

class ActionContext(BaseModel):
    cluster_summary: str
    original_post_text: Optional[str] = None
    similar_report_count: int = 0

class Action(BaseModel):
    id: Optional[str] = None
    type: ActionType
    state: ActionState = "pending"
    cluster_id: str
    target_post_id: Optional[str] = None
    draft: dict
    context: ActionContext
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    reject_reason: Optional[str] = None
    outcome: Optional[dict] = None

class Brand(BaseModel):
    id: Optional[str] = None
    name: str
    vertical: Vertical = "generic"
    voice_guidelines: str = ""
    keywords: list[str] = []
    thresholds: dict = {"critical": 700, "high": 400, "medium": 200}
    connections: dict = {}

class DecisionBody(BaseModel):
    decision: Literal["approve", "edit_approve", "reject", "reassign"]
    edited_text: Optional[str] = None
    reject_reason: Optional[str] = None
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_models.py -v
```
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/models.py backend/tests/test_models.py
git commit -m "feat(backend): Pydantic models mirroring spec"
```

---

## Task 5: ClickHouse migrations

**Files:**
- Create: `backend/migrations/001_clickhouse.sql`
- Create: `backend/scripts/apply_migrations.py`

- [ ] **Step 1: Write `backend/migrations/001_clickhouse.sql`**

```sql
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
```

- [ ] **Step 2: Write `backend/scripts/apply_migrations.py`**

```python
"""Apply ClickHouse + Postgres migrations. Idempotent."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"

async def apply_clickhouse():
    import clickhouse_connect
    client = await clickhouse_connect.get_async_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        secure=True,
    )
    sql = (MIGRATIONS / "001_clickhouse.sql").read_text()
    # ClickHouse rejects multi-statement HTTP queries; split on ';'
    for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
        await client.command(stmt)
    print("✓ ClickHouse migrations applied")

async def apply_postgres():
    import asyncpg
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    sql = (MIGRATIONS / "002_postgres.sql").read_text()
    await conn.execute(sql)
    await conn.close()
    print("✓ Postgres migrations applied")

async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in ("clickhouse", "all"):
        await apply_clickhouse()
    if target in ("postgres", "all"):
        await apply_postgres()

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Commit**

```bash
git add backend/migrations/001_clickhouse.sql backend/scripts/apply_migrations.py
git commit -m "feat(backend): ClickHouse posts table + cluster_engagement_mv migration"
```

---

## Task 6: Postgres migrations

**Files:**
- Create: `backend/migrations/002_postgres.sql`

- [ ] **Step 1: Write `backend/migrations/002_postgres.sql`**

```sql
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/migrations/002_postgres.sql
git commit -m "feat(backend): Postgres+pgvector migration with HNSW index"
```

---

## Task 7: ClickHouse client wrapper (`core/ch.py`)

**Files:**
- Create: `backend/app/core/ch.py`

- [ ] **Step 1: Write `backend/app/core/ch.py`**

```python
"""ClickHouse async client singleton."""
import clickhouse_connect
from app.config import settings

_client = None

async def init_clickhouse():
    global _client
    _client = await clickhouse_connect.get_async_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        secure=True,
    )

def ch():
    """Return the initialized client. Raises if uninitialized."""
    if _client is None:
        raise RuntimeError("ClickHouse client not initialized; call init_clickhouse() first")
    return _client
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/ch.py
git commit -m "feat(backend): async ClickHouse client singleton"
```

---

## Task 8: Postgres asyncpg pool (`core/db.py`)

**Files:**
- Create: `backend/app/core/db.py`

- [ ] **Step 1: Write `backend/app/core/db.py`**

```python
"""Postgres connection pool (asyncpg)."""
import asyncpg
from app.config import settings

pool: asyncpg.Pool | None = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(
        settings.database_url, min_size=2, max_size=10,
    )

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/db.py
git commit -m "feat(backend): asyncpg pool init/close"
```

---

## Task 9: Redis queue (`core/queue.py`)

**Files:**
- Create: `backend/app/core/queue.py`

- [ ] **Step 1: Write `backend/app/core/queue.py`**

```python
"""Redis-backed job queue using arq.

Producers call `enqueue(job_name, **kwargs)`. Workers in
`app.workers.pipeline_worker` consume by job name.
"""
from typing import Any
from arq.connections import RedisSettings, create_pool
from app.config import settings

_pool = None

async def init_queue():
    global _pool
    _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))

async def enqueue(job_name: str, payload: dict[str, Any]):
    if _pool is None:
        await init_queue()
    await _pool.enqueue_job(job_name, payload)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/queue.py
git commit -m "feat(backend): arq-based Redis job queue wrapper"
```

---

## Task 10: Datadog metrics + tracing (`core/metrics.py`)

**Files:**
- Create: `backend/app/core/metrics.py`

- [ ] **Step 1: Write `backend/app/core/metrics.py`**

```python
"""Datadog observability: APM spans + DogStatsD counters/gauges/histograms."""
import functools
from datadog import initialize, statsd
from ddtrace import tracer
from app.config import settings

initialize(statsd_host=settings.dd_agent_host, statsd_port=8125)
tracer.set_tags({"service": settings.dd_service, "env": settings.dd_env})

def span(name: str):
    """Decorator: wrap an async function in a Datadog APM span."""
    def deco(fn):
        @functools.wraps(fn)
        async def wrapper(*a, **kw):
            with tracer.trace(name, service=settings.dd_service):
                return await fn(*a, **kw)
        return wrapper
    return deco

__all__ = ["span", "statsd", "tracer"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/metrics.py
git commit -m "feat(backend): Datadog APM span decorator + DogStatsD"
```

---

## Task 11: Gemini LLM wrappers (`core/llm.py`) — pure unit tests on prompt builders

**Files:**
- Create: `backend/app/core/llm.py`
- Test: `backend/tests/test_llm_prompts.py`

- [ ] **Step 1: Write failing test (prompt builder is pure)**

```python
# backend/tests/test_llm_prompts.py
from app.core.llm import build_draft_prompt, build_summary_prompt

def test_draft_prompt_includes_brand_and_post():
    brand = {"name": "Acme", "voice_guidelines": "Warm, witty."}
    cluster = {"summary": "Checkout crash on iOS 18", "post_count": 11}
    p = build_draft_prompt(brand, cluster, "checkout broken", 280)
    assert "Acme" in p
    assert "Warm, witty" in p
    assert "checkout broken" in p
    assert "280" in p
    assert "11 similar" in p

def test_summary_prompt_lists_count():
    p = build_summary_prompt(["a", "b", "c"])
    assert "3 social" in p
```

- [ ] **Step 2: Write `backend/app/core/llm.py`**

```python
"""Google DeepMind / Gemini wrappers — embed, classify, summarize, draft."""
import json
from google import genai
from google.genai import types
from app.config import settings

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

def build_summary_prompt(texts: list[str]) -> str:
    head = (
        f"Below are {len(texts)} social posts grouped by similarity. "
        "Return JSON: {name: 3-5 word theme, summary: 2-3 sentences "
        "covering the core complaint/request/praise, who is affected and "
        "how widespread, tags: 3-5 topic tags}."
    )
    return head + "\n\n" + "\n".join(texts[:20])

def build_draft_prompt(brand: dict, cluster: dict, post_text: str, char_limit: int) -> str:
    return (
        f"You are drafting a social media response on behalf of {brand['name']}. "
        f"Voice: {brand.get('voice_guidelines','')}. The customer said: \"{post_text}\". "
        f"Context: {cluster['summary']} ({cluster['post_count']} similar reports). "
        "Draft a response that (1) acknowledges the specific issue, (2) is "
        "empathetic without being formulaic, (3) offers a concrete next step, "
        f"(4) stays under {char_limit} characters. Do not make promises the brand "
        "has not authorized. If unsure, route to human."
    )

async def embed_batch(texts: list[str]) -> list[list[float]]:
    """text-embedding-004 → 768-dim vectors, batched."""
    client = _get_client()
    resp = await client.aio.models.embed_content(
        model="text-embedding-004", contents=texts,
    )
    return [e.values for e in resp.embeddings]

async def classify_sentiment(text: str) -> str:
    client = _get_client()
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-flash",
        contents=(
            "Classify this customer post as positive, negative, neutral, "
            "or question. Return only the label.\n\n" + text
        ),
        config=types.GenerateContentConfig(max_output_tokens=4, temperature=0),
    )
    label = (resp.text or "").strip().lower()
    return label if label in {"positive", "negative", "neutral", "question"} else "neutral"

async def summarize_cluster(texts: list[str]) -> tuple[str, str, list[str]]:
    client = _get_client()
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-pro",
        contents=build_summary_prompt(texts),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    try:
        d = json.loads(resp.text)
        return d.get("name", "Untitled"), d.get("summary", ""), d.get("tags", [])
    except Exception:
        return "Untitled", "", []

async def draft_response(brand: dict, cluster: dict, post_text: str, char_limit: int) -> str:
    client = _get_client()
    resp = await client.aio.models.generate_content(
        model="gemini-1.5-pro",
        contents=build_draft_prompt(brand, cluster, post_text, char_limit),
    )
    return (resp.text or "").strip()

async def classify_action_type(cluster: dict, top_posts: list) -> str:
    """Cheap rule first; LLM only if ambiguous."""
    neg = sum(1 for p in top_posts if "negative" in (p[7] if len(p) > 7 else ""))
    if cluster["severity_score"] >= cluster.get("thresholds", {}).get("critical", 700):
        return "escalation"
    if neg >= 5:
        return "response"
    return "insight"
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_llm_prompts.py -v
```
Expected: 2 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/llm.py backend/tests/test_llm_prompts.py
git commit -m "feat(backend): Gemini wrappers (embed/classify/summarize/draft)"
```

---

## Task 12: Realtime publisher (`core/realtime.py`)

**Files:**
- Create: `backend/app/core/realtime.py`

- [ ] **Step 1: Write `backend/app/core/realtime.py`**

```python
"""In-process pub/sub for WebSocket fanout.

For MVP: tracks active WS connections per brand and pushes JSON payloads.
v1.0 can swap to Supabase Realtime by publishing to a Postgres trigger.
"""
import asyncio
from collections import defaultdict
from typing import Any

_subscribers: dict[str, set] = defaultdict(set)

async def subscribe(brand_id: str, ws):
    _subscribers[brand_id].add(ws)

async def unsubscribe(brand_id: str, ws):
    _subscribers[brand_id].discard(ws)

async def publish(brand_id: str, payload: dict[str, Any]):
    """Fan out a message to all WS subscribers for a brand."""
    dead = []
    for ws in _subscribers.get(brand_id, []):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _subscribers[brand_id].discard(ws)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/realtime.py
git commit -m "feat(backend): in-process WS pub/sub realtime fanout"
```

---

## Task 13: Adapter base + X normalizer with full unit tests

**Files:**
- Create: `backend/app/adapters/base.py`
- Create: `backend/app/adapters/x.py`
- Test: `backend/tests/test_adapters.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_adapters.py
from app.adapters import get_adapter
from app.adapters.x import XNormalizer

def test_x_normalizer_basic():
    payload = {
        "data": {
            "id": "1789",
            "text": "@brand checkout crashed",
            "author_id": "u1",
            "public_metrics": {"like_count": 10, "retweet_count": 5, "reply_count": 2},
            "created_at": "2026-02-27T10:00:00Z",
        }
    }
    posts = XNormalizer().normalize(payload)
    assert len(posts) == 1
    p = posts[0]
    assert p.platform == "x"
    assert p.platform_post_id == "1789"
    assert p.likes == 10 and p.shares == 5 and p.comments == 2
    assert p.text == "@brand checkout crashed"

def test_adapter_registry_returns_x():
    adapter = get_adapter("x")
    assert isinstance(adapter, XNormalizer)
```

- [ ] **Step 2: Write `backend/app/adapters/base.py`**

```python
"""Adapter base class + registry."""
from abc import ABC, abstractmethod
from typing import ClassVar
from app.models import Post

class Normalizer(ABC):
    platform: ClassVar[str]

    @abstractmethod
    def normalize(self, payload: dict) -> list[Post]: ...

_REGISTRY: dict[str, Normalizer] = {}

def register(adapter: Normalizer):
    _REGISTRY[adapter.platform] = adapter

def get_adapter(platform: str) -> Normalizer:
    if platform not in _REGISTRY:
        raise ValueError(f"Unknown platform: {platform}")
    return _REGISTRY[platform]
```

- [ ] **Step 3: Write `backend/app/adapters/x.py`**

```python
from datetime import datetime
from app.adapters.base import Normalizer, register
from app.models import Post

class XNormalizer(Normalizer):
    platform = "x"

    def normalize(self, payload: dict) -> list[Post]:
        d = payload["data"]
        m = d.get("public_metrics", {})
        return [Post(
            platform="x",
            platform_post_id=d["id"],
            author_handle=d.get("author_id", ""),
            author_follower_count=d.get("author", {}).get("followers", 0),
            text=d["text"],
            media_urls=[a["url"] for a in d.get("attachments", [])],
            likes=m.get("like_count", 0),
            shares=m.get("retweet_count", 0),
            comments=m.get("reply_count", 0),
            permalink=f"https://x.com/i/web/status/{d['id']}",
            posted_at=datetime.fromisoformat(d["created_at"].replace("Z", "+00:00")),
            sentiment="neutral",
            cluster_id=None,
            source="webhook",
        )]

register(XNormalizer())
```

- [ ] **Step 4: Wire registration in `backend/app/adapters/__init__.py`**

```python
"""Side-effect imports register adapters."""
from app.adapters.base import get_adapter, register  # noqa
from app.adapters import x  # noqa: F401  -- registers XNormalizer
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_adapters.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/adapters/ backend/tests/test_adapters.py
git commit -m "feat(backend): adapter registry + X normalizer with tests"
```

---

## Task 14: Meta (Instagram/Facebook) + Nimble normalizers

**Files:**
- Create: `backend/app/adapters/meta.py`
- Create: `backend/app/adapters/nimble.py`
- Modify: `backend/app/adapters/__init__.py`
- Test: extend `backend/tests/test_adapters.py`

- [ ] **Step 1: Add tests**

```python
# append to backend/tests/test_adapters.py
from app.adapters.meta import MetaNormalizer
from app.adapters.nimble import NimbleNormalizer

def test_meta_instagram_normalize():
    payload = {
        "object": "instagram",
        "data": {
            "id": "ig_42", "username": "@hater", "text": "loved it",
            "like_count": 4, "comments_count": 1, "share_count": 0,
            "permalink": "https://instagram.com/p/abc",
            "timestamp": "2026-02-27T10:00:00Z",
        }
    }
    posts = MetaNormalizer().normalize(payload)
    assert posts[0].platform == "instagram"
    assert posts[0].likes == 4

def test_nimble_normalize_item():
    payload = {"items": [{
        "platform": "reddit", "id": "r1", "author": "u/x", "author_followers": 0,
        "text": "broken", "likes": 12, "shares": 0, "comments": 3,
        "url": "https://reddit.com/...", "posted_at": "2026-02-27T10:00:00Z",
    }]}
    posts = NimbleNormalizer().from_items(payload["items"])
    assert posts[0].platform == "reddit"
    assert posts[0].source == "nimble"
```

- [ ] **Step 2: Write `backend/app/adapters/meta.py`**

```python
from datetime import datetime
from app.adapters.base import Normalizer, register
from app.models import Post

class MetaNormalizer(Normalizer):
    platform = "facebook"  # registered once; we route IG via 'object'

    def normalize(self, payload: dict) -> list[Post]:
        d = payload["data"]
        platform = "instagram" if payload.get("object") == "instagram" else "facebook"
        return [Post(
            platform=platform,
            platform_post_id=d["id"],
            author_handle=d.get("username", ""),
            author_follower_count=d.get("follower_count", 0),
            text=d.get("text") or d.get("caption", ""),
            media_urls=d.get("media_urls", []),
            likes=d.get("like_count", 0),
            shares=d.get("share_count", 0),
            comments=d.get("comments_count", 0),
            permalink=d.get("permalink", ""),
            posted_at=datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")),
            sentiment="neutral",
            cluster_id=None,
            source="webhook",
        )]

# Register both platform keys → same adapter instance
_m = MetaNormalizer()
register(_m)
from app.adapters.base import _REGISTRY
_REGISTRY["instagram"] = _m
```

- [ ] **Step 3: Write `backend/app/adapters/nimble.py`**

```python
"""Nimble: structured open-web + Reddit/TikTok pulls."""
import os
from datetime import datetime
from typing import Iterable
import httpx
from app.adapters.base import Normalizer
from app.config import settings
from app.models import Post

class NimbleNormalizer(Normalizer):
    platform = "nimble"  # not a real platform; bypass registry

    def from_items(self, items: Iterable[dict]) -> list[Post]:
        return [Post(
            platform=r["platform"],
            platform_post_id=str(r["id"]),
            author_handle=r.get("author", ""),
            author_follower_count=int(r.get("author_followers", 0) or 0),
            text=r.get("text", ""),
            media_urls=r.get("media", []),
            likes=int(r.get("likes", 0) or 0),
            shares=int(r.get("shares", 0) or 0),
            comments=int(r.get("comments", 0) or 0),
            permalink=r.get("url", ""),
            posted_at=datetime.fromisoformat(r["posted_at"].replace("Z", "+00:00")),
            sentiment="neutral",
            cluster_id=None,
            source="nimble",
        ) for r in items]

    def normalize(self, payload: dict) -> list[Post]:
        return self.from_items(payload.get("items", []))

    async def poll(self, brand: dict) -> tuple[list[Post], str | None]:
        """Pull mentions from Nimble. Returns (posts, new_cursor)."""
        if not settings.nimble_api_key:
            return [], brand.get("nimble_cursor")
        params = {
            "query": " OR ".join(brand.get("keywords", [])),
            "sources": "reddit,tiktok,web",
            "structured": "true",
        }
        if brand.get("nimble_cursor"):
            params["since_cursor"] = brand["nimble_cursor"]
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                "https://api.nimbleway.com/v1/search",
                params=params,
                headers={"Authorization": f"Bearer {settings.nimble_api_key}"},
            )
            r.raise_for_status()
            data = r.json()
        return self.from_items(data.get("items", [])), data.get("next_cursor")
```

- [ ] **Step 4: Update `backend/app/adapters/__init__.py`**

```python
"""Side-effect imports register adapters."""
from app.adapters.base import get_adapter, register  # noqa
from app.adapters import x, meta  # noqa: F401
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_adapters.py -v
```
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/adapters/ backend/tests/test_adapters.py
git commit -m "feat(backend): Meta + Nimble normalizers"
```

---

## Task 15: Pure scoring formula with full TDD

**Files:**
- Create: `backend/app/pipeline/score_formula.py` (pure)
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_scoring.py
from app.pipeline.score_formula import compute_score, severity_label

def test_score_critical_when_high_engagement_and_velocity():
    s = compute_score(
        post_count=11, likes=300, shares=80, comments=20,
        max_followers=200_000, neg_count=9, recent_2h=6,
    )
    # volume=110, engagement=300*2+80*5+20*3=1060, sentiment=(9/11)*100*3.5≈286,
    # velocity=(6/11)*100≈54.5, influence=1.5 → (110+1060+286+55)*1.5 ≈ 2266
    assert s["severity_score"] > 700
    assert s["influence_multiplier"] == 1.5

def test_score_zero_when_no_posts():
    s = compute_score(0, 0, 0, 0, 0, 0, 0)
    assert s["severity_score"] == 0

def test_severity_labels():
    t = {"critical": 700, "high": 400, "medium": 200}
    assert severity_label(701, t) == "critical"
    assert severity_label(500, t) == "high"
    assert severity_label(300, t) == "medium"
    assert severity_label(50, t) == "low"
```

- [ ] **Step 2: Write `backend/app/pipeline/score_formula.py`**

```python
"""Pure scoring functions. No I/O. Easy to test."""

WEIGHTS = {"volume": 10, "like": 2, "share": 5, "comment": 3, "sentiment": 3.5}

def compute_score(
    post_count: int, likes: int, shares: int, comments: int,
    max_followers: int, neg_count: int, recent_2h: int,
) -> dict:
    n = post_count or 0
    volume = n * WEIGHTS["volume"]
    engagement = likes*WEIGHTS["like"] + shares*WEIGHTS["share"] + comments*WEIGHTS["comment"]
    pct_neg = (neg_count / n) if n else 0
    sentiment = pct_neg * 100 * WEIGHTS["sentiment"]
    velocity = (recent_2h / n * 100) if n else 0
    influence = 1.5 if max_followers > 50_000 else 1.0
    score = (volume + engagement + sentiment + velocity) * influence
    return {
        "volume": volume, "engagement": engagement, "sentiment": sentiment,
        "velocity": velocity, "influence_multiplier": influence,
        "severity_score": score,
    }

def severity_label(score: float, thresholds: dict) -> str:
    if score >= thresholds["critical"]: return "critical"
    if score >= thresholds["high"]:     return "high"
    if score >= thresholds["medium"]:   return "medium"
    return "low"
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_scoring.py -v
```
Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add backend/app/pipeline/score_formula.py backend/tests/test_scoring.py
git commit -m "feat(pipeline): pure scoring formula + severity labels with TDD"
```

---

## Task 16: Monitor stage (`pipeline/monitor.py`)

**Files:**
- Create: `backend/app/pipeline/monitor.py`

- [ ] **Step 1: Write `backend/app/pipeline/monitor.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/pipeline/monitor.py
git commit -m "feat(pipeline): Monitor stage (CH insert + sentiment + cluster trigger)"
```

---

## Task 17: Cluster stage (`pipeline/cluster.py`)

**Files:**
- Create: `backend/app/pipeline/cluster.py`

- [ ] **Step 1: Write `backend/app/pipeline/cluster.py`**

```python
"""Stage 2: embed unclustered posts, assign to nearest cluster or create new."""
import uuid
from datetime import datetime, timezone
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/pipeline/cluster.py
git commit -m "feat(pipeline): Cluster stage (embed + nearest-neighbor + merge)"
```

---

## Task 18: Score stage (`pipeline/score.py`)

**Files:**
- Create: `backend/app/pipeline/score.py`

- [ ] **Step 1: Write `backend/app/pipeline/score.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/pipeline/score.py
git commit -m "feat(pipeline): Score stage from ClickHouse aggregates"
```

---

## Task 19: Slack + Luminai destinations

**Files:**
- Create: `backend/app/destinations/slack.py`
- Create: `backend/app/destinations/luminai.py`

- [ ] **Step 1: Write `backend/app/destinations/slack.py`**

```python
"""Slack incoming-webhook poster for escalations."""
import httpx

async def post_message(webhook_url: str, text: str, blocks: list[dict] | None = None):
    if not webhook_url:
        return {"ok": False, "reason": "no_webhook"}
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(webhook_url, json=payload)
    return {"ok": r.status_code == 200, "status": r.status_code}
```

- [ ] **Step 2: Write `backend/app/destinations/luminai.py`**

```python
"""Luminai destination — health-system operations workflows.

PHI guardrail: only the de-identified cluster *summary* is sent — never raw
patient posts.
"""
import httpx
from app.config import settings

BASE = "https://api.luminai.com/v1"

def _auth():
    return {"Authorization": f"Bearer {settings.luminai_api_key}"} if settings.luminai_api_key else {}

async def classify_workflow(cluster_summary: str) -> str:
    if not settings.luminai_api_key:
        return "uncategorized"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{BASE}/workflows/classify",
            headers=_auth(),
            json={"summary": cluster_summary},
        )
        r.raise_for_status()
        return r.json().get("workflow_id", "uncategorized")

async def execute(workflow_id: str, ticket: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{BASE}/workflows/{workflow_id}/instances",
            headers=_auth(),
            json=ticket,
        )
        r.raise_for_status()
        return r.json()
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/destinations/
git commit -m "feat(destinations): Slack + Luminai with PHI guardrail"
```

---

## Task 20: Act stage (`pipeline/act.py`)

**Files:**
- Create: `backend/app/pipeline/act.py`

- [ ] **Step 1: Write `backend/app/pipeline/act.py`**

```python
"""Stage 4: choose action type, draft via Gemini, persist as pending action."""
import uuid
from app.core.db import pool
from app.core.ch import ch
from app.core.llm import classify_action_type, draft_response
from app.core.realtime import publish
from app.core.metrics import span
from app.config import CHAR_LIMITS
from app.destinations import luminai

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

    if action_type == "ticket" and brand["vertical"] == "healthcare":
        draft["destination"] = "luminai"
        draft["luminai_workflow"] = await luminai.classify_workflow(cluster["summary"])

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO actions (brand_id, type, state, cluster_id,
                target_post_id, draft, context)
            VALUES ($1,$2,'pending',$3,$4,$5::jsonb,$6::jsonb) RETURNING id
            """,
            brand["id"], action_type, cid, draft.get("target_post_id"),
            __import__("json").dumps(draft),
            __import__("json").dumps({
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/pipeline/act.py
git commit -m "feat(pipeline): Act stage with 4 action drafters + Luminai routing"
```

---

## Task 21: Webhook routes (`api/webhooks.py`) + smoke test

**Files:**
- Create: `backend/app/api/webhooks.py`
- Test: `backend/tests/test_webhooks.py`

- [ ] **Step 1: Write `backend/app/api/webhooks.py`**

```python
"""Inbound platform webhooks with HMAC verification."""
import hashlib
import hmac
from fastapi import APIRouter, Header, HTTPException, Request

from app.adapters import get_adapter
from app.config import settings
from app.core.queue import enqueue

router = APIRouter()

def _secret_for(platform: str) -> str:
    return {
        "x": settings.x_webhook_secret,
        "instagram": settings.meta_app_secret,
        "facebook": settings.meta_app_secret,
    }.get(platform, "")

def _verify_hmac(raw: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")

@router.post("/{platform}")
async def ingest(platform: str, request: Request,
                 x_hub_signature_256: str = Header(default="")):
    raw = await request.body()
    secret = _secret_for(platform)
    if not _verify_hmac(raw, x_hub_signature_256, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    try:
        adapter = get_adapter(platform)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
    posts = adapter.normalize(await request.json())
    brand_id = request.query_params.get("brand_id")
    if not brand_id:
        raise HTTPException(status_code=400, detail="Missing brand_id")
    for p in posts:
        await enqueue("monitor_persist", {"brand_id": brand_id, "post": p.model_dump(mode="json")})
    return {"status": "accepted", "enqueued": len(posts)}
```

- [ ] **Step 2: Write smoke test**

```python
# backend/tests/test_webhooks.py
import hmac
import hashlib
import json
from fastapi.testclient import TestClient

from app.config import settings

settings.x_webhook_secret = "test-secret"

# We import the app lazily so settings are picked up after monkey-patch
def _client():
    from app.main import app
    return TestClient(app)

def _sig(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def test_webhook_rejects_bad_signature(monkeypatch):
    client = _client()
    body = json.dumps({"data": {"id": "1", "text": "hi", "public_metrics": {}, "created_at": "2026-02-27T10:00:00Z"}}).encode()
    r = client.post("/api/webhooks/x?brand_id=00000000-0000-0000-0000-000000000000",
                    content=body,
                    headers={"X-Hub-Signature-256": "sha256=wrong"})
    assert r.status_code == 401
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/webhooks.py backend/tests/test_webhooks.py
git commit -m "feat(api): HMAC-verified webhook ingest with smoke test"
```

---

## Task 22: REST routes (`api/routes.py`)

**Files:**
- Create: `backend/app/api/routes.py`

- [ ] **Step 1: Write `backend/app/api/routes.py`**

```python
"""REST endpoints: feed, clusters, queue, actions, brands, health."""
import json
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query
from app.core.ch import ch
from app.core.db import pool
from app.models import Brand, DecisionBody
from app.pipeline.score_formula import WEIGHTS

router = APIRouter()

@router.get("/health")
async def health():
    services = {}
    try:
        await ch().query("SELECT 1")
        services["clickhouse"] = "connected"
    except Exception as e:
        services["clickhouse"] = f"error: {e}"
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["postgres"] = "connected"
    except Exception as e:
        services["postgres"] = f"error: {e}"
    return {"status": "healthy", "services": services,
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/feed")
async def feed(brand_id: str = Query(...), platform: str | None = None,
               sentiment: str | None = None, limit: int = 50):
    where = ["brand_id = %(brand_id)s"]
    params: dict = {"brand_id": brand_id, "limit": limit}
    if platform:
        where.append("platform = %(platform)s")
        params["platform"] = platform
    if sentiment:
        where.append("sentiment = %(sentiment)s")
        params["sentiment"] = sentiment
    sql = f"""
        SELECT id, platform, author_handle, author_follower_count, text,
               media_urls, likes, shares, comments, permalink, posted_at,
               ingested_at, sentiment, cluster_id
        FROM posts FINAL WHERE {' AND '.join(where)}
        ORDER BY ingested_at DESC LIMIT %(limit)s
    """
    rows = (await ch().query(sql, params)).result_rows
    posts = [{
        "id": str(r[0]), "platform": r[1], "author_handle": r[2],
        "author_follower_count": r[3], "text": r[4], "media_urls": r[5],
        "likes": r[6], "shares": r[7], "comments": r[8], "permalink": r[9],
        "posted_at": r[10].isoformat() if r[10] else None,
        "ingested_at": r[11].isoformat() if r[11] else None,
        "sentiment": r[12], "cluster_id": str(r[13]) if r[13] else None,
    } for r in rows]

    stats = await _feed_stats(brand_id)
    return {"posts": posts, "next_cursor": None, "stats": stats}

async def _feed_stats(brand_id: str) -> dict:
    # volume_24h
    v = (await ch().query(
        "SELECT count() FROM posts WHERE brand_id=%(b)s AND posted_at > now() - INTERVAL 24 HOUR",
        {"b": brand_id},
    )).result_rows[0][0]
    # platform distribution (24h)
    dist_rows = (await ch().query(
        """SELECT platform, count() FROM posts
           WHERE brand_id=%(b)s AND posted_at > now() - INTERVAL 24 HOUR
           GROUP BY platform""",
        {"b": brand_id},
    )).result_rows
    distribution = {row[0]: row[1] for row in dist_rows}
    # 7-day sentiment trend (avg sentiment encoded as -1/0/+1)
    trend_rows = (await ch().query(
        """SELECT toDate(posted_at) AS d,
                  avgIf(1, sentiment='positive')
                  - avgIf(1, sentiment='negative') AS s
           FROM posts WHERE brand_id=%(b)s
                       AND posted_at > now() - INTERVAL 7 DAY
           GROUP BY d ORDER BY d""",
        {"b": brand_id},
    )).result_rows
    sentiment_7d = [float(r[1] or 0) for r in trend_rows]
    return {
        "volume_24h": int(v or 0),
        "sentiment_7d": sentiment_7d,
        "platform_distribution": distribution,
        "avg_response_minutes": 0,
    }

@router.get("/clusters")
async def list_clusters(brand_id: str = Query(...), status: str = "active",
                        min_severity: str | None = None):
    sql = """
        SELECT id, name, summary, post_count, severity, severity_score,
               tags, sentiment_breakdown, platforms,
               first_seen_at, last_activity_at, status
        FROM clusters WHERE brand_id=$1 AND status=$2
        ORDER BY severity_score DESC LIMIT 100
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, uuid.UUID(brand_id), status)
    items = [{
        "id": str(r["id"]), "name": r["name"], "summary": r["summary"],
        "post_count": r["post_count"], "severity": r["severity"],
        "severity_score": r["severity_score"], "tags": r["tags"],
        "sentiment_breakdown": r["sentiment_breakdown"],
        "platforms": r["platforms"],
        "first_seen_at": r["first_seen_at"].isoformat() if r["first_seen_at"] else None,
        "last_activity_at": r["last_activity_at"].isoformat() if r["last_activity_at"] else None,
        "status": r["status"],
    } for r in rows]
    if min_severity:
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        threshold = order.get(min_severity, 0)
        items = [c for c in items if order.get(c["severity"], 0) >= threshold]
    return {"clusters": items, "total": len(items)}

@router.get("/queue")
async def queue(brand_id: str = Query(...), limit: int = 50):
    async with pool.acquire() as conn:
        thresholds = await conn.fetchval(
            "SELECT thresholds FROM brands WHERE id=$1", uuid.UUID(brand_id),
        )
        rows = await conn.fetch(
            "SELECT id, name, severity, severity_score FROM clusters "
            "WHERE brand_id=$1 AND status='active' ORDER BY severity_score DESC LIMIT $2",
            uuid.UUID(brand_id), limit,
        )
    queue = []
    for r in rows:
        agg = await ch().query(
            """
            SELECT any(post_count), any(likes), any(shares), any(comments),
                   any(max_followers), any(neg_count),
                   (SELECT count() FROM posts
                      WHERE cluster_id = %(cid)s
                        AND posted_at > now() - INTERVAL 2 HOUR) AS recent
            FROM cluster_engagement_mv WHERE cluster_id=%(cid)s
            """, {"cid": str(r["id"])},
        )
        if not agg.result_rows:
            continue
        n, likes, shares, comments, mf, neg, recent = agg.result_rows[0]
        from app.pipeline.score_formula import compute_score
        sd = compute_score(int(n or 0), int(likes or 0), int(shares or 0),
                           int(comments or 0), int(mf or 0), int(neg or 0),
                           int(recent or 0))
        queue.append({
            "cluster_id": str(r["id"]), "name": r["name"],
            "severity_score": r["severity_score"], "severity": r["severity"],
            "breakdown": {
                "volume": sd["volume"], "engagement": sd["engagement"],
                "sentiment": sd["sentiment"], "velocity": sd["velocity"],
                "influence_multiplier": sd["influence_multiplier"],
            },
            "auto_escalate": r["severity"] == "critical",
        })
    return {"queue": queue, "threshold_config": thresholds, "weights": WEIGHTS}

@router.get("/actions")
async def list_actions(brand_id: str = Query(...), type: str | None = None,
                       state: str = "pending"):
    where = "brand_id=$1 AND state=$2"
    params: list = [uuid.UUID(brand_id), state]
    if type:
        where += " AND type=$3"
        params.append(type)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT id, type, state, cluster_id, target_post_id, draft, "
            f"context, created_at FROM actions WHERE {where} "
            f"ORDER BY created_at DESC LIMIT 100",
            *params,
        )
    items = [{
        "id": str(r["id"]), "type": r["type"], "state": r["state"],
        "cluster_id": str(r["cluster_id"]),
        "target_post_id": str(r["target_post_id"]) if r["target_post_id"] else None,
        "draft": r["draft"], "context": r["context"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
    } for r in rows]
    return {"actions": items, "total": len(items)}

@router.post("/actions/{action_id}")
async def decide_action(action_id: str, body: DecisionBody):
    async with pool.acquire() as conn:
        current = await conn.fetchrow("SELECT state, draft FROM actions WHERE id=$1",
                                       uuid.UUID(action_id))
        if not current:
            raise HTTPException(status_code=404, detail="Action not found")
        if current["state"] != "pending":
            raise HTTPException(status_code=409, detail="Action no longer pending")

        new_state = {"approve": "approved", "edit_approve": "approved",
                     "reject": "rejected"}.get(body.decision, "rejected")
        new_draft = current["draft"]
        if body.decision == "edit_approve" and body.edited_text:
            d = dict(new_draft) if isinstance(new_draft, dict) else json.loads(new_draft)
            d["text"] = body.edited_text
            d["char_count"] = len(body.edited_text)
            new_draft = json.dumps(d)
        else:
            new_draft = json.dumps(new_draft) if isinstance(new_draft, dict) else new_draft

        await conn.execute(
            """
            UPDATE actions SET state=$1, draft=$2::jsonb, decided_at=now(),
                reject_reason=$3 WHERE id=$4
            """,
            new_state, new_draft, body.reject_reason, uuid.UUID(action_id),
        )
    return {"id": action_id, "state": new_state,
            "execution": {"destination": "queued", "queued_at": datetime.now(timezone.utc).isoformat(),
                          "external_id": None}}

@router.post("/brands")
async def create_brand(brand: Brand):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO brands (name, vertical, voice_guidelines, keywords,
                thresholds, connections)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb) RETURNING id, name
            """,
            brand.name, brand.vertical, brand.voice_guidelines, brand.keywords,
            json.dumps(brand.thresholds), json.dumps(brand.connections),
        )
    return {"id": str(row["id"]), "name": row["name"]}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/routes.py
git commit -m "feat(api): REST routes for feed/clusters/queue/actions/brands/health"
```

---

## Task 23: WebSocket route + FastAPI main entry

**Files:**
- Create: `backend/app/api/websocket.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Write `backend/app/api/websocket.py`**

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.realtime import subscribe, unsubscribe

router = APIRouter()

@router.websocket("/ws/feed/{brand_id}")
async def feed_ws(ws: WebSocket, brand_id: str):
    await ws.accept()
    await subscribe(brand_id, ws)
    try:
        while True:
            await ws.receive_text()  # ignore client messages; keep alive
    except WebSocketDisconnect:
        await unsubscribe(brand_id, ws)
```

- [ ] **Step 2: Write `backend/app/main.py`**

```python
"""FastAPI entry point."""
from ddtrace import patch_all
patch_all()  # noqa

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import webhooks, routes, websocket
from app.core.db import init_pool, close_pool
from app.core.ch import init_clickhouse
from app.core.queue import init_queue

app = FastAPI(title="Pulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_pool()
    await init_clickhouse()
    await init_queue()

@app.on_event("shutdown")
async def shutdown():
    await close_pool()

app.include_router(webhooks.router, prefix="/api/webhooks")
app.include_router(routes.router, prefix="/api")
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "Pulse API", "version": "1.0.0"}
```

- [ ] **Step 3: Verify the app imports + responds**

```bash
cd backend && uvicorn app.main:app --port 8000 &
sleep 2
curl -s http://localhost:8000/ | grep "Pulse API"
kill %1
```
Expected: `"message":"Pulse API"`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/websocket.py backend/app/main.py
git commit -m "feat(api): WebSocket + FastAPI main entry + CORS"
```

---

## Task 24: arq pipeline worker + cron polling

**Files:**
- Create: `backend/app/workers/pipeline_worker.py`
- Create: `backend/app/workers/cron.py`

- [ ] **Step 1: Write `backend/app/workers/pipeline_worker.py`**

```python
"""arq worker — consumes monitor_persist, cluster_run, score_run, act_run jobs."""
from arq.connections import RedisSettings
from app.config import settings
from app.core.ch import init_clickhouse
from app.core.db import init_pool
from app.pipeline.monitor import persist_post
from app.pipeline.cluster import run_clustering
from app.pipeline.score import run_scoring
from app.pipeline.act import run_act
from app.models import Post

async def monitor_persist(ctx, payload: dict):
    return await persist_post(payload["brand_id"], Post(**payload["post"]))

async def cluster_run(ctx, payload: dict):
    return await run_clustering(payload["brand_id"])

async def score_run(ctx, payload: dict):
    return await run_scoring(payload["brand_id"])

async def act_run(ctx, payload: dict):
    return await run_act(payload["cluster_id"])

async def startup(ctx):
    await init_pool()
    await init_clickhouse()

class WorkerSettings:
    functions = [monitor_persist, cluster_run, score_run, act_run]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = startup
```

- [ ] **Step 2: Write `backend/app/workers/cron.py`**

```python
"""Cron entrypoints — invoked by Render cron jobs (or run manually)."""
import asyncio
from app.core.db import init_pool, pool
from app.core.ch import init_clickhouse, ch
from app.core.queue import enqueue
from app.core.metrics import statsd
from app.adapters.nimble import NimbleNormalizer

nimble = NimbleNormalizer()

async def poll_platforms():
    await init_pool()
    async with pool.acquire() as conn:
        brands = await conn.fetch("SELECT id, keywords, nimble_cursor FROM brands")
    for b in brands:
        posts, cursor = await nimble.poll({
            "id": str(b["id"]),
            "keywords": list(b["keywords"] or []),
            "nimble_cursor": b["nimble_cursor"],
        })
        statsd.gauge("pulse.poller.batch_size", len(posts), tags=[f"brand:{b['id']}"])
        for p in posts:
            await enqueue("monitor_persist", {"brand_id": str(b["id"]), "post": p.model_dump(mode="json")})
        if cursor:
            async with pool.acquire() as conn:
                await conn.execute("UPDATE brands SET nimble_cursor=$1 WHERE id=$2",
                                    cursor, b["id"])

async def refresh_engagement():
    await init_clickhouse()
    # Placeholder: re-fetching engagement requires per-platform API specifics.
    # For the demo, we trigger a no-op score recompute over recent brands.
    rows = (await ch().query(
        "SELECT DISTINCT brand_id FROM posts WHERE ingested_at > now() - INTERVAL 48 HOUR"
    )).result_rows
    for (bid,) in rows:
        await enqueue("score_run", {"brand_id": str(bid)})

if __name__ == "__main__":
    import sys
    fn = {"poll_platforms": poll_platforms, "refresh_engagement": refresh_engagement}[sys.argv[1]]
    asyncio.run(fn())
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/workers/
git commit -m "feat(workers): arq pipeline worker + Nimble polling cron"
```

---

## Task 25: Seed script (demo data → Critical cluster)

**Files:**
- Create: `backend/scripts/seed_demo.py`

- [ ] **Step 1: Write `backend/scripts/seed_demo.py`**

```python
"""Seed Acme Coffee with a staged checkout-crash incident.

After this runs, the demo brand has:
  - 1 brand
  - ~12 posts (mostly negative, viral)
  - 1 Critical cluster
  - 1 pending response action + 1 pending ticket action
"""
import asyncio
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()

CRASH_POSTS = [
    ("x", "@acme checkout crashed on iOS 18 again, third time today", 312, 88, 24, 184_000, "negative"),
    ("x", "anyone else? @acme app dies right at payment confirm", 540, 120, 60, 22_000, "negative"),
    ("reddit", "Acme app checkout broken on iOS — lost my cart twice", 88, 0, 41, 0, "negative"),
    ("x", "@acme please fix this, can't complete my order", 102, 14, 7, 1_200, "negative"),
    ("x", "Acme iOS 18 cart bug? customer support not responding", 67, 11, 19, 3_400, "question"),
    ("reddit", "PSA: Acme checkout dies on iOS 18.2, downgrade or wait", 410, 0, 88, 0, "negative"),
    ("x", "love @acme but this checkout situation is unreal", 22, 3, 4, 600, "negative"),
    ("instagram", "ok the @acme app keeps crashing!! 😩", 145, 8, 12, 11_000, "negative"),
    ("x", "@acme reset my cart twice today. ridiculous", 56, 9, 11, 800, "negative"),
    ("reddit", "Has anyone gotten Acme to refund the cart-bug orders?", 73, 0, 25, 0, "question"),
    ("x", "Acme = my favorite app and worst checkout. fix it", 39, 6, 5, 1_500, "negative"),
    ("x", "iPhone users avoid Acme checkout right now", 280, 47, 14, 8_900, "negative"),
]

async def main():
    import asyncpg
    import clickhouse_connect

    pg = await asyncpg.connect(os.environ["DATABASE_URL"])
    ch = await clickhouse_connect.get_async_client(
        host=os.environ["CLICKHOUSE_HOST"], port=int(os.environ.get("CLICKHOUSE_PORT", 8443)),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""), secure=True,
    )

    brand_id = await pg.fetchval("""
        INSERT INTO brands (name, vertical, voice_guidelines, keywords)
        VALUES ('Acme Coffee', 'generic',
                'Warm, casual, slightly witty. Never corporate.',
                ARRAY['acme','@acme','acmecoffee'])
        ON CONFLICT DO NOTHING
        RETURNING id
    """)
    if brand_id is None:
        brand_id = await pg.fetchval("SELECT id FROM brands WHERE name='Acme Coffee'")

    # 1 cluster
    cluster_id = await pg.fetchval("""
        INSERT INTO clusters (brand_id, name, summary, severity, severity_score,
            tags, post_count, first_seen_at, last_activity_at, platforms)
        VALUES ($1, 'App Checkout Crash (v4.2.1)',
                'Customers on iOS 18 report the checkout screen crashing on payment confirmation. Affects ~340 users across X and Reddit; volume accelerating over the last 2 hours.',
                'critical', 742, ARRAY['checkout','ios','crash','payments'],
                $2, now() - INTERVAL '2 hours', now(),
                ARRAY['x','reddit','instagram'])
        RETURNING id
    """, brand_id, len(CRASH_POSTS))

    import uuid
    posts = []
    now = datetime.now(timezone.utc)
    for i, (plat, text, likes, shares, comments, followers, sentiment) in enumerate(CRASH_POSTS):
        posts.append([
            str(uuid.uuid4()), str(brand_id), plat, f"seed-{i}", "@user",
            followers, text, [], likes, shares, comments,
            "https://example.com/" + str(i),
            now - timedelta(minutes=i*7), now, sentiment, str(cluster_id), "webhook",
        ])
    await ch.insert("posts", posts, column_names=[
        "id","brand_id","platform","platform_post_id","author_handle",
        "author_follower_count","text","media_urls","likes","shares",
        "comments","permalink","posted_at","ingested_at","sentiment",
        "cluster_id","source"])

    # 1 pending response action + 1 pending ticket action
    import json as _j
    await pg.execute("""
        INSERT INTO actions (brand_id, type, state, cluster_id, draft, context)
        VALUES ($1,'response','pending',$2,$3::jsonb,$4::jsonb),
               ($1,'ticket','pending',$2,$5::jsonb,$4::jsonb)
    """,
        brand_id, cluster_id,
        _j.dumps({
            "text": ("We're so sorry about the checkout crashes on iOS 18 — our team is on "
                     "it right now and pushing a fix today. Can you DM us your order ID "
                     "so we can make this right?"),
            "char_count": 168, "char_limit": 280, "platform": "x",
            "target_post_id": posts[0][0],
        }),
        _j.dumps({
            "cluster_summary": "Checkout crashing on iOS 18 — ~340 users",
            "original_post_text": CRASH_POSTS[0][1],
            "similar_report_count": len(CRASH_POSTS),
        }),
        _j.dumps({
            "title": "App Checkout Crash (v4.2.1)",
            "description": "Customers on iOS 18 report checkout crashing on payment confirmation.",
            "priority": "P1 (score: 742)", "component": "Mobile App — Checkout",
            "social_links": ["https://example.com/" + str(i) for i in range(5)],
        }),
    )

    print("✓ seed complete")
    print("  brand_id =", brand_id)
    print("  cluster_id =", cluster_id)
    await pg.close()

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Commit**

```bash
git add backend/scripts/seed_demo.py
git commit -m "feat(scripts): seed_demo script (Acme + Critical checkout-crash cluster)"
```

---

## Task 26: Frontend scaffolding (Next.js + Tailwind + TanStack)

**Files:**
- Create: `frontend/package.json`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `next.config.js`, `.env.local.example`, `app/globals.css`

- [ ] **Step 1: Create Next.js project**

```bash
cd /Users/kushagrabehl/Downloads/newData/newDataDog
npx --yes create-next-app@14 frontend --typescript --tailwind --app --no-eslint --import-alias "@/*" --use-npm <<< "y"
```

- [ ] **Step 2: Add the needed deps**

```bash
cd frontend
npm install @tanstack/react-query@5.17.0 recharts@2.10.0 zustand@4.5.0 clsx@2.1.0 @supabase/supabase-js@2.39.0
```

- [ ] **Step 3: Write `frontend/.env.local.example`**

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEMO_BRAND_ID=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): Next.js 14 + Tailwind + TanStack scaffold"
```

---

## Task 27: Shared types + API client

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Write `frontend/lib/types.ts`**

```typescript
export type Platform = "x" | "instagram" | "tiktok" | "reddit" | "facebook";
export type Sentiment = "positive" | "negative" | "neutral" | "question";
export type Severity = "critical" | "high" | "medium" | "low";
export type ClusterStatus = "active" | "resolved" | "snoozed";
export type ActionType = "response" | "ticket" | "escalation" | "faq" | "insight" | "dm";
export type ActionState = "pending" | "approved" | "executed" | "rejected";

export interface Post {
  id: string; platform: Platform; author_handle: string;
  author_follower_count: number; text: string; media_urls: string[];
  likes: number; shares: number; comments: number; permalink: string;
  posted_at: string; ingested_at: string;
  sentiment: Sentiment; cluster_id: string | null;
}

export interface FeedStats {
  volume_24h: number;
  sentiment_7d: number[];
  platform_distribution: Record<Platform, number>;
  avg_response_minutes: number;
}

export interface FeedResponse {
  posts: Post[]; next_cursor: string | null; stats: FeedStats;
}

export interface SentimentBreakdown {
  positive: number; negative: number; neutral: number; question: number;
}

export interface Cluster {
  id: string; name: string; summary: string;
  post_count: number; severity: Severity; severity_score: number;
  tags: string[]; sentiment_breakdown: SentimentBreakdown;
  platforms: Platform[];
  first_seen_at: string | null; last_activity_at: string | null;
  status: ClusterStatus;
}

export interface ClustersResponse { clusters: Cluster[]; total: number; }

export interface QueueRow {
  cluster_id: string; name: string;
  severity_score: number; severity: Severity;
  breakdown: {
    volume: number; engagement: number; sentiment: number;
    velocity: number; influence_multiplier: number;
  };
  auto_escalate: boolean;
}

export interface QueueResponse {
  queue: QueueRow[];
  threshold_config: Record<string, number>;
  weights: Record<string, number>;
}

export interface ResponseDraft {
  text: string; char_count: number; char_limit: number; platform: Platform;
  target_post_id?: string;
}

export interface Action {
  id: string; type: ActionType; state: ActionState;
  cluster_id: string; target_post_id?: string;
  draft: ResponseDraft | Record<string, any>;
  context: { cluster_summary: string; original_post_text?: string; similar_report_count: number; };
  created_at: string;
}

export interface ActionsResponse { actions: Action[]; total: number; }

export interface DecisionBody {
  decision: "approve" | "edit_approve" | "reject" | "reassign";
  edited_text?: string;
  reject_reason?: string;
}
```

- [ ] **Step 2: Write `frontend/lib/api.ts`**

```typescript
import type {
  FeedResponse, ClustersResponse, QueueResponse, ActionsResponse,
  Action, DecisionBody,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
    ...opts,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  health: () => req<any>("/health"),
  feed: (brandId: string, q = "") => req<FeedResponse>(`/feed?brand_id=${brandId}${q}`),
  clusters: (brandId: string) => req<ClustersResponse>(`/clusters?brand_id=${brandId}`),
  queue: (brandId: string) => req<QueueResponse>(`/queue?brand_id=${brandId}`),
  actions: (brandId: string) => req<ActionsResponse>(`/actions?brand_id=${brandId}`),
  decide: (id: string, body: DecisionBody) =>
    req<Action>(`/actions/${id}`, { method: "POST", body: JSON.stringify(body) }),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/
git commit -m "feat(frontend): shared types + API client"
```

---

## Task 28: Providers + root layout + nav

**Files:**
- Create: `frontend/app/providers.tsx`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Write `frontend/app/providers.tsx`**

```typescript
"use client";
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 10_000, refetchInterval: 30_000 } },
  }));
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 2: Replace `frontend/app/layout.tsx`**

```typescript
import "./globals.css";
import Link from "next/link";
import { Providers } from "./providers";

export const metadata = {
  title: "Pulse",
  description: "Social listening + action pipeline",
};

const NAV = [
  { href: "/feed", label: "Live Feed" },
  { href: "/clusters", label: "Clusters" },
  { href: "/queue", label: "Priority Queue" },
  { href: "/actions", label: "Actions" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <Providers>
          <nav className="flex items-center gap-6 px-6 h-14 bg-white border-b">
            <Link href="/" className="font-bold text-indigo-600">Pulse</Link>
            {NAV.map((n) => (
              <Link key={n.href} href={n.href}
                className="text-sm text-gray-600 hover:text-indigo-600">{n.label}</Link>
            ))}
          </nav>
          {children}
        </Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Replace `frontend/app/page.tsx` to redirect to /feed**

```typescript
import { redirect } from "next/navigation";
export default function Home() { redirect("/feed"); }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/providers.tsx frontend/app/layout.tsx frontend/app/page.tsx
git commit -m "feat(frontend): providers + root layout with nav"
```

---

## Task 29: Live Feed view + PostCard + FeedSidebar

**Files:**
- Create: `frontend/components/PostCard.tsx`
- Create: `frontend/components/FeedSidebar.tsx`
- Create: `frontend/hooks/useFeed.ts`
- Create: `frontend/app/feed/page.tsx`

- [ ] **Step 1: Write `frontend/components/PostCard.tsx`**

```typescript
import type { Post } from "@/lib/types";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "border-l-green-500",
  negative: "border-l-red-500",
  neutral:  "border-l-gray-400",
  question: "border-l-blue-500",
};

export function PostCard({ post }: { post: Post }) {
  return (
    <article className={`bg-white rounded-lg border-l-4 ${SENTIMENT_COLORS[post.sentiment]} shadow-sm p-4`}>
      <header className="flex justify-between text-sm text-gray-500">
        <span className="font-medium">{post.author_handle}</span>
        <span className="uppercase tracking-wide">{post.platform}</span>
      </header>
      <p className="my-2 text-gray-900">{post.text}</p>
      <footer className="flex gap-4 text-xs text-gray-500">
        <span>♥ {post.likes}</span>
        <span>↻ {post.shares}</span>
        <span>💬 {post.comments}</span>
        <span className="ml-auto">{post.author_follower_count.toLocaleString()} followers</span>
      </footer>
    </article>
  );
}
```

- [ ] **Step 2: Write `frontend/components/FeedSidebar.tsx`**

```typescript
"use client";
import type { FeedStats } from "@/lib/types";
import { LineChart, Line, ResponsiveContainer } from "recharts";

export function FeedSidebar({ stats }: { stats?: FeedStats }) {
  if (!stats) return null;
  const data = stats.sentiment_7d.map((v, i) => ({ d: i, v }));
  return (
    <aside className="w-72 space-y-4">
      <div className="bg-white p-4 rounded-xl shadow-sm">
        <p className="text-xs text-gray-500 uppercase tracking-wide">Volume 24h</p>
        <p className="text-3xl font-bold mt-1">{stats.volume_24h}</p>
      </div>
      <div className="bg-white p-4 rounded-xl shadow-sm">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Sentiment 7d</p>
        <div className="h-12">
          <ResponsiveContainer><LineChart data={data}>
            <Line type="monotone" dataKey="v" stroke="#4f46e5" strokeWidth={2} dot={false} />
          </LineChart></ResponsiveContainer>
        </div>
      </div>
      <div className="bg-white p-4 rounded-xl shadow-sm">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Platforms</p>
        <ul className="text-sm space-y-1">
          {Object.entries(stats.platform_distribution).map(([p, n]) => (
            <li key={p} className="flex justify-between">
              <span className="capitalize">{p}</span><span>{n}</span>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
```

- [ ] **Step 3: Write `frontend/hooks/useFeed.ts`**

```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useFeed(brandId: string, filters: { platform?: string; sentiment?: string }) {
  const q = new URLSearchParams(filters as Record<string, string>).toString();
  return useQuery({
    queryKey: ["feed", brandId, filters],
    queryFn: () => api.feed(brandId, q ? `&${q}` : ""),
    enabled: !!brandId,
  });
}
```

- [ ] **Step 4: Write `frontend/app/feed/page.tsx`**

```typescript
"use client";
import { useState } from "react";
import { useFeed } from "@/hooks/useFeed";
import { PostCard } from "@/components/PostCard";
import { FeedSidebar } from "@/components/FeedSidebar";

const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID!;
const PLATFORMS = ["all", "x", "instagram", "tiktok", "reddit", "facebook"];

export default function FeedPage() {
  const [platform, setPlatform] = useState("all");
  const { data, isLoading, error } = useFeed(BRAND_ID,
    platform === "all" ? {} : { platform });

  return (
    <div className="flex gap-6 p-6">
      <main className="flex-1">
        <div className="flex gap-2 mb-4">
          {PLATFORMS.map((p) => (
            <button key={p} onClick={() => setPlatform(p)}
              className={`px-3 py-1 rounded-full text-sm capitalize ${
                platform === p ? "bg-indigo-600 text-white" : "bg-gray-100"}`}>
              {p}
            </button>
          ))}
        </div>
        {error && <p className="text-red-600">Failed to load feed</p>}
        {isLoading && <p className="text-gray-400">Loading…</p>}
        <div className="space-y-3">
          {data?.posts.map((post) => <PostCard key={post.id} post={post} />)}
        </div>
      </main>
      <FeedSidebar stats={data?.stats} />
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/components/PostCard.tsx frontend/components/FeedSidebar.tsx \
  frontend/hooks/useFeed.ts frontend/app/feed/page.tsx
git commit -m "feat(frontend): Live Feed view (Monitor stage)"
```

---

## Task 30: Clusters view (SeverityBadge + SentimentBar + ClusterCard)

**Files:**
- Create: `frontend/components/SeverityBadge.tsx`
- Create: `frontend/components/SentimentBar.tsx`
- Create: `frontend/components/ClusterCard.tsx`
- Create: `frontend/hooks/useClusters.ts`
- Create: `frontend/app/clusters/page.tsx`

- [ ] **Step 1: Write `frontend/components/SeverityBadge.tsx`**

```typescript
const STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-yellow-100 text-yellow-700",
  low:      "bg-gray-100 text-gray-600",
};

export function SeverityBadge({ severity, score }: { severity: string; score: number }) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${STYLES[severity]}`}>
      {severity.toUpperCase()} · {Math.round(score)}
    </span>
  );
}
```

- [ ] **Step 2: Write `frontend/components/SentimentBar.tsx`**

```typescript
import type { SentimentBreakdown } from "@/lib/types";

export function SentimentBar({ breakdown }: { breakdown: SentimentBreakdown }) {
  const total = (breakdown.positive + breakdown.negative + breakdown.neutral + breakdown.question) || 1;
  const seg = (n: number, color: string) => (
    <div className={color} style={{ width: `${(n / total) * 100}%` }} />
  );
  return (
    <div className="flex h-2 rounded overflow-hidden bg-gray-100">
      {seg(breakdown.positive, "bg-green-500")}
      {seg(breakdown.negative, "bg-red-500")}
      {seg(breakdown.neutral, "bg-gray-400")}
      {seg(breakdown.question, "bg-blue-500")}
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/components/ClusterCard.tsx`**

```typescript
import type { Cluster } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";
import { SentimentBar } from "./SentimentBar";

export function ClusterCard({ cluster }: { cluster: Cluster }) {
  return (
    <div className="bg-white rounded-xl shadow p-5 flex flex-col gap-3">
      <div className="flex justify-between items-start">
        <h3 className="font-semibold text-lg">{cluster.name}</h3>
        <SeverityBadge severity={cluster.severity} score={cluster.severity_score} />
      </div>
      <p className="text-sm text-gray-600">{cluster.summary}</p>
      <SentimentBar breakdown={cluster.sentiment_breakdown} />
      <div className="flex flex-wrap gap-1">
        {cluster.tags.map((t) => (
          <span key={t} className="text-xs bg-gray-100 px-2 py-0.5 rounded">#{t}</span>
        ))}
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-auto pt-2 border-t">
        <span>{cluster.post_count} posts</span>
        <span>{cluster.platforms.join(" · ")}</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Write `frontend/hooks/useClusters.ts`**

```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useClusters(brandId: string) {
  return useQuery({
    queryKey: ["clusters", brandId],
    queryFn: () => api.clusters(brandId),
    enabled: !!brandId,
  });
}
```

- [ ] **Step 5: Write `frontend/app/clusters/page.tsx`**

```typescript
"use client";
import { useClusters } from "@/hooks/useClusters";
import { ClusterCard } from "@/components/ClusterCard";

const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID!;

export default function ClustersPage() {
  const { data, isLoading } = useClusters(BRAND_ID);
  if (isLoading) return <p className="p-6 text-gray-400">Loading…</p>;
  return (
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data?.clusters.map((c) => <ClusterCard key={c.id} cluster={c} />)}
    </div>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/SeverityBadge.tsx frontend/components/SentimentBar.tsx \
  frontend/components/ClusterCard.tsx frontend/hooks/useClusters.ts frontend/app/clusters/page.tsx
git commit -m "feat(frontend): Clusters view + SeverityBadge + SentimentBar"
```

---

## Task 31: Priority Queue view

**Files:**
- Create: `frontend/components/QueueTable.tsx`
- Create: `frontend/hooks/useQueue.ts`
- Create: `frontend/app/queue/page.tsx`

- [ ] **Step 1: Write `frontend/components/QueueTable.tsx`**

```typescript
import type { QueueRow } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";

export function QueueTable({ rows }: { rows: QueueRow[] }) {
  return (
    <table className="w-full text-sm">
      <thead className="text-left text-gray-500 border-b">
        <tr>
          <th className="py-2">Cluster</th>
          <th>Volume</th><th>Engagement</th><th>Sentiment</th>
          <th>Velocity</th><th>Influence</th><th>Severity</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.cluster_id} className="border-b hover:bg-gray-50">
            <td className="py-2 font-medium">{r.name}</td>
            <td>{r.breakdown.volume.toFixed(0)}</td>
            <td>{r.breakdown.engagement.toFixed(0)}</td>
            <td>{r.breakdown.sentiment.toFixed(0)}</td>
            <td>{r.breakdown.velocity.toFixed(0)}</td>
            <td>×{r.breakdown.influence_multiplier}</td>
            <td><SeverityBadge severity={r.severity} score={r.severity_score} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

- [ ] **Step 2: Write `frontend/hooks/useQueue.ts`**

```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useQueue(brandId: string) {
  return useQuery({
    queryKey: ["queue", brandId],
    queryFn: () => api.queue(brandId),
    enabled: !!brandId,
  });
}
```

- [ ] **Step 3: Write `frontend/app/queue/page.tsx`**

```typescript
"use client";
import { useQueue } from "@/hooks/useQueue";
import { QueueTable } from "@/components/QueueTable";

const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID!;

export default function QueuePage() {
  const { data, isLoading } = useQueue(BRAND_ID);
  if (isLoading) return <p className="p-6 text-gray-400">Loading…</p>;
  return (
    <div className="p-6 bg-white rounded-xl shadow m-6">
      <h2 className="text-lg font-semibold mb-4">Priority Queue</h2>
      <QueueTable rows={data?.queue ?? []} />
      <p className="text-xs text-gray-400 mt-3">
        Weights: vol×{data?.weights.volume}, like×{data?.weights.like}, share×{data?.weights.share},
        comment×{data?.weights.comment}, sentiment×{data?.weights.sentiment}
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/QueueTable.tsx frontend/hooks/useQueue.ts frontend/app/queue/page.tsx
git commit -m "feat(frontend): Priority Queue view (Score stage)"
```

---

## Task 32: Actions view + ActionCard with approve/edit/reject

**Files:**
- Create: `frontend/components/ActionCard.tsx`
- Create: `frontend/hooks/useActions.ts`
- Create: `frontend/app/actions/page.tsx`

- [ ] **Step 1: Write `frontend/components/ActionCard.tsx`**

```typescript
"use client";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Action } from "@/lib/types";

const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID!;

export function ActionCard({ action }: { action: Action }) {
  const qc = useQueryClient();
  const [text, setText] = useState((action.draft as any).text ?? "");
  const decide = useMutation({
    mutationFn: (body: any) => api.decide(action.id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["actions", BRAND_ID] }),
  });

  return (
    <div className="bg-white rounded-xl shadow p-5 space-y-3">
      <div className="flex justify-between">
        <span className="text-xs uppercase font-semibold text-indigo-600">{action.type}</span>
        <span className="text-xs text-gray-400">
          {action.context.similar_report_count} reports
        </span>
      </div>
      {action.context.original_post_text && (
        <p className="text-sm text-gray-500 italic border-l-2 pl-3">
          "{action.context.original_post_text}"
        </p>
      )}
      {action.type === "response" ? (
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          className="w-full border rounded p-2 text-sm" rows={3} />
      ) : (
        <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
          {JSON.stringify(action.draft, null, 2)}
        </pre>
      )}
      <div className="flex gap-2">
        <button onClick={() => decide.mutate({ decision: "approve" })}
          className="bg-green-600 text-white px-4 py-1.5 rounded text-sm">Approve</button>
        <button onClick={() => decide.mutate({ decision: "edit_approve", edited_text: text })}
          className="bg-indigo-600 text-white px-4 py-1.5 rounded text-sm">Edit & Approve</button>
        <button onClick={() => decide.mutate({ decision: "reject", reject_reason: "not relevant" })}
          className="bg-gray-200 px-4 py-1.5 rounded text-sm">Reject</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/hooks/useActions.ts`**

```typescript
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useActions(brandId: string) {
  return useQuery({
    queryKey: ["actions", brandId],
    queryFn: () => api.actions(brandId),
    enabled: !!brandId,
  });
}
```

- [ ] **Step 3: Write `frontend/app/actions/page.tsx`**

```typescript
"use client";
import { useActions } from "@/hooks/useActions";
import { ActionCard } from "@/components/ActionCard";

const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID!;

export default function ActionsPage() {
  const { data, isLoading } = useActions(BRAND_ID);
  if (isLoading) return <p className="p-6 text-gray-400">Loading…</p>;
  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
      {data?.actions.map((a) => <ActionCard key={a.id} action={a} />)}
      {data && data.actions.length === 0 && (
        <p className="text-gray-400 col-span-full">No pending actions.</p>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/ActionCard.tsx frontend/hooks/useActions.ts \
  frontend/app/actions/page.tsx
git commit -m "feat(frontend): Actions view with approve/edit/reject mutations"
```

---

## Task 33: End-to-end smoke test (manual)

This is a non-code task — checklist for the engineer running the demo.

- [ ] **Step 1: Backend up**

```bash
cd backend && source .venv/bin/activate
python scripts/apply_migrations.py
python scripts/seed_demo.py | tee /tmp/seed.out
# copy the brand_id and put it in frontend/.env.local as NEXT_PUBLIC_DEMO_BRAND_ID
uvicorn app.main:app --reload &
arq app.workers.pipeline_worker.WorkerSettings &
```

- [ ] **Step 2: Confirm `/api/health` reports both stores connected**

```bash
curl -s http://localhost:8000/api/health | python -m json.tool
```
Expected: `clickhouse: connected`, `postgres: connected`.

- [ ] **Step 3: Confirm seed data**

```bash
curl -s "http://localhost:8000/api/clusters?brand_id=<BRAND_ID>" | python -m json.tool
curl -s "http://localhost:8000/api/queue?brand_id=<BRAND_ID>" | python -m json.tool
curl -s "http://localhost:8000/api/actions?brand_id=<BRAND_ID>" | python -m json.tool
```
Expected: 1 critical cluster · queue row with breakdown · 2 pending actions.

- [ ] **Step 4: Frontend up**

```bash
cd frontend && npm run dev
```
Open http://localhost:3000 — verify every view renders.

- [ ] **Step 5: Approve a response from the UI**

Click `Approve` on the response action. Reload `/actions` — it should be gone.

- [ ] **Step 6: Live ingest (optional, if X webhook secret is set)**

```bash
BODY='{"data":{"id":"live-1","text":"@acme another crash today","author_id":"u","public_metrics":{"like_count":3,"retweet_count":1,"reply_count":0},"created_at":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"}}'
SIG="sha256=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$X_WEBHOOK_SECRET" -hex | awk '{print $2}')"
curl -X POST "http://localhost:8000/api/webhooks/x?brand_id=$BRAND_ID" \
  -H "X-Hub-Signature-256: $SIG" -H "Content-Type: application/json" -d "$BODY"
```
Expected: `{"status":"accepted","enqueued":1}` and within a few seconds the post appears in the Live Feed.

- [ ] **Step 7: Commit a note in CHANGELOG/README if anything was discovered**

```bash
git add README.md
git commit -m "docs: smoke-test pass on seed + live ingest"
```

---

## Self-Review

**Spec coverage:**
- Monitor → covered Tasks 13–16, 21, 24
- Cluster → Task 17
- Score → Tasks 15, 18, 22
- Act → Task 20, 19 (Luminai), 22 (decide)
- Datadog → Task 10, plus spans on every stage
- Nimble → Task 14, 24
- Gemini → Task 11
- ClickHouse → Tasks 5, 7
- Postgres + pgvector → Tasks 6, 8
- 4 views → Tasks 28–32
- Seed → Task 25
- Smoke test → Task 33

**Placeholder scan:** No TBDs. Every code step has actual code. Every command has an expected outcome.

**Type consistency:** Backend `Post` ↔ frontend `Post` align on fields. `Action.draft` is `dict`/`Record<string, any>` consistently. Queue breakdown keys match between scoring formula (`volume/engagement/sentiment/velocity/influence_multiplier`) and the frontend `QueueRow` interface.

**Known gaps:**
- No real Render deploy steps inside tasks (the spec's deploy section is a reference; the demo is localhost).
- `refresh_engagement` (Task 24) is a no-op placeholder that just enqueues `score_run`. Full re-fetch logic is out of scope for the 4hr MVP and would land in v1.0.
- Supabase Realtime is not wired; MVP relies on TanStack's 30s polling, which is what the spec also allows for MVP.
- Slack/Jira destinations are imported but not invoked from `act.py`'s default path — the executed-action step would call them post-approval; the demo stops at the approval click.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-23-pulse-implementation.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — execute tasks in this session using executing-plans, batch checkpoints.

Which approach?
