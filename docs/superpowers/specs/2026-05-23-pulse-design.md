# Pulse — Social Listening & Action Pipeline - Technical Design Document

**Project Name:** Pulse
**Hackathon:** Autonomous Agents Hackathon 2026
**Build Time:** 4 hours (MVP) + 1-2 hours (Extensions)
**Team Structure:** 2-3 developers (Frontend + Backend)

> **Status:** Auto-approved by user 2026-05-23. This is the authoritative spec. Supersedes the earlier brainstormed "autonomy-loop / Crosby GEO" design — user explicitly handed this in as "the intended design.md for the record" and instructed: "approve everything and move on... we need to move to implementation asap."

## Hackathon Requirements Compliance

✅ **Use at least 3 sponsor tools** (Pulse uses 5 + supporting infra):

| Sponsor | Tagline | Role in Pulse | Stage |
|---------|---------|---------------|-------|
| 🔍 **Nimble** | Web data your agents can trust | Reliable, structured ingestion of brand mentions across the open web + platforms | Monitor |
| 🧠 **Google DeepMind** | The research lab redefining what's possible | Gemini models for sentiment classification, cluster summarization, and response drafting | Cluster / Act |
| 🏠 **ClickHouse** | The database built for speed | Append-heavy time-series store for posts, engagement, and analytics that drive scoring | Score / Dashboard |
| 🐶 **Datadog** | See everything your stack is doing | Full observability across the 4-stage pipeline: queue depth, per-stage latency, post-to-action SLO | All stages |
| ⛑️ **Luminai** | The AI Platform for Health System Operations | Action-execution layer for the **healthcare vertical** — routes operational tickets into health-system workflows (v2) | Act |

Supporting infra (not sponsor-track, but required): Supabase (Postgres + pgvector for transactional + vector data), Upstash Redis (job queue), Render (deployment), Twitter/X API v2 (Filtered Stream).

## Pipeline (Monitor → Cluster → Score → Act)

Pulse runs as a four-stage event-driven pipeline. Each stage is a discrete service triggered by the previous via the job queue.

| Stage | Input | Output | Trigger |
|-------|-------|--------|---------|
| **Monitor** | Platform webhooks / polling | Normalized posts in ClickHouse | Real-time (webhook) or 60s polling |
| **Cluster** | New posts with embeddings | Themed clusters with summaries | Batch every 5 min or 50 new posts |
| **Score** | Clusters with post counts | Severity-ranked priority list | On cluster update |
| **Act** | Scored clusters above threshold | Draft responses, tickets, escalations | On score exceeding threshold |

### Stage 1 — Monitor
1. **Webhook Listener** — FastAPI endpoints receive real-time events from X / Instagram / Facebook. Per-platform adapter normalizes payload. HMAC verify.
2. **Nimble Collector** — Cron 60s pulls brand mentions from Reddit / TikTok / open web. Structured + anti-bot. Cursor per source.
3. **Deduplication** — `(platform, platform_post_id)` keyed. ClickHouse `ReplacingMergeTree` keeps latest snapshot at merge.
4. **Sentiment** — Inline `gemini-1.5-flash` returns `positive | negative | neutral | question` (~200ms).
5. **Engagement Refresh** — 15-min job re-fetches metrics for posts <48h old, appends new ClickHouse snapshot rows.

### Stage 2 — Cluster
- Batch embed unclustered posts (max 100/call) via `text-embedding-004` (768-dim).
- Cosine nearest-neighbor over pgvector. If sim > **0.82** → assign existing cluster.
- Else create cluster; `gemini-1.5-pro` generates name + summary from founding post.
- Centroids with sim > **0.88** → merge + regen summary.
- Summary regen on +5 posts or every 30 min.

### Stage 3 — Score
Five-factor severity, all inputs from one ClickHouse aggregation over the `cluster_engagement_mv` SummingMergeTree plus a live 2h window query.

| Component | Formula |
|---|---|
| Volume | `post_count × 10` |
| Engagement | `Σlikes×2 + Σshares×5 + Σcomments×3` |
| Sentiment | `pct_negative × 3.5` |
| Velocity | `posts_last_2h / posts_total × 100` |
| Influence | `× 1.5` if `max_followers > 50K` |

**Thresholds:** Critical 700+ · High 400–699 · Medium 200–399 · Low <200. **Decay:** ×0.8 daily after 24h idle.

### Stage 4 — Act
Six action types auto-selected by cluster characteristics. Drafting uses `gemini-1.5-pro` with brand-voice prompt:
- **Draft Response** — ≥5 negative/question posts → platform API
- **Support Ticket** — bug/operational → Jira / Linear / Zendesk, or **Luminai** for healthcare brands
- **Escalation Alert** — score ≥700 or velocity spike >50%/2h → Slack / email
- **FAQ Update** — ≥3 "question" posts on same topic → CMS
- **Product Insight** — feature requests → product backlog
- **DM Follow-up** — high severity + identifiable user → platform DM

**Human-in-the-loop:** `Pending → Approved → Executed` (plus `Rejected`). Nothing posts without explicit approval.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Next.js + TS + Tailwind + TanStack Query           │
│   - LiveFeed (Monitor) · Clusters · PriorityQueue · Actions  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST + WS / Supabase Realtime
┌──────────────────────┴──────────────────────────────────────┐
│ BACKEND: FastAPI                                             │
│   POST /api/webhooks/{platform}   (HMAC-verified)            │
│   GET  /api/feed | /clusters | /queue | /actions             │
│   POST /api/actions/{id}          (approve/edit/reject)      │
│   WS   /ws/feed/{brand_id}                                   │
│   Services: MonitorService · ClusterService                  │
│             ScoreService   · ActService                      │
└──────────────────────┬──────────────────────────────────────┘
        ┌──────────────┼───────────────┬───────────────┐
        │              │               │               │
   ┌────▼─────┐  ┌────▼─────┐   ┌─────▼─────┐   ┌──────▼──────┐
   │ClickHouse│  │  Redis   │   │  Workers  │   │ 🧠 Gemini   │
   │ posts +  │  │  Queue   │   │ cluster   │   │ embed/      │
   │ analytics│  │ (Upstash)│   │ score/act │   │ classify/   │
   │ (TS)     │  │          │   │           │   │ summ/draft  │
   └──────────┘  └──────────┘   └───────────┘   └─────────────┘
        │                                              │
   ┌────▼──────────┐   INGRESS                ┌────────▼────────┐
   │ Postgres +    │   🔍 Nimble ─▶ Monitor   │ ACTION EGRESS   │
   │ pgvector      │   (open web + platform)  │ Slack / Jira /  │
   │ (clusters,    │                          │ ⛑️ Luminai      │
   │  actions)     │                          │                 │
   └───────────────┘                          └─────────────────┘
   🐶 Datadog traces every box · SLO post-to-action <2 min
```

## API Contract

**Base URL:** `http://localhost:8000` (dev) / `https://pulse-api.onrender.com` (prod)
**Auth:** `Authorization: Bearer <supabase-jwt>` (REST) / `X-Hub-Signature-256: sha256=<hmac>` (webhooks)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/webhooks/{platform}` | Inbound platform events (HMAC-verified). 202 + enqueue. |
| GET  | `/api/feed?brand_id=` | Reverse-chrono posts + stats (volume_24h, sentiment_7d, distribution). |
| GET  | `/api/clusters?brand_id=&status=&min_severity=` | Active clusters sorted by severity. |
| GET  | `/api/queue?brand_id=` | Ranked clusters with full score breakdown + thresholds + weights. |
| GET  | `/api/actions?brand_id=&type=&state=` | Pending action drafts. |
| POST | `/api/actions/{id}` | `{decision: approve\|edit_approve\|reject, edited_text?, reject_reason?}` |
| POST | `/api/brands` · PATCH `/api/brands/{id}` | Brand onboarding + config (voice, keywords, thresholds, connections). |
| WS   | `/ws/feed/{brand_id}` | Realtime push: `new_post`, `cluster_update`, `action_created`, `escalation`. |
| GET  | `/api/health` | All sponsor connections + queue depth. |

## Data Models (TypeScript — Pydantic mirrors)

```typescript
type Platform = "x" | "instagram" | "tiktok" | "reddit" | "facebook";
type Sentiment = "positive" | "negative" | "neutral" | "question";
type Severity = "critical" | "high" | "medium" | "low";
type ClusterStatus = "active" | "resolved" | "snoozed";
type ActionType = "response" | "ticket" | "escalation" | "faq" | "insight" | "dm";
type ActionState = "pending" | "approved" | "executed" | "rejected";

interface Post {
  id: string; platform: Platform; platform_post_id: string;
  author_handle: string; author_follower_count: number;
  text: string; media_urls: string[];
  likes: number; shares: number; comments: number;
  permalink: string; posted_at: string; ingested_at: string;
  embedding?: number[]; sentiment: Sentiment; cluster_id: string | null;
}

interface Cluster {
  id: string; brand_id: string; name: string; summary: string;
  centroid?: number[]; post_count: number;
  severity: Severity; severity_score: number;
  tags: string[]; sentiment_breakdown: SentimentBreakdown;
  platforms: Platform[]; first_seen_at: string; last_activity_at: string;
  status: ClusterStatus;
}

interface ScoreBreakdown {
  cluster_id: string;
  volume: number; engagement: number; sentiment: number;
  velocity: number; influence_multiplier: number;
  severity_score: number; severity: Severity; auto_escalate: boolean;
}

interface Action {
  id: string; type: ActionType; state: ActionState;
  cluster_id: string; target_post_id?: string;
  draft: ResponseDraft | TicketDraft | EscalationDraft | Record<string, any>;
  context: { cluster_summary: string; original_post_text?: string; similar_report_count: number; };
  created_at: string; decided_at?: string; decided_by?: string;
  reject_reason?: string; outcome?: ActionOutcome;
}

interface Brand {
  id: string; name: string; vertical: "generic" | "healthcare";
  voice_guidelines: string; keywords: string[];
  thresholds: { critical: number; high: number; medium: number };
  connections: Record<Platform | "slack" | "jira" | "linear" | "cms", string>;
}
```

## Database Schema

**ClickHouse — posts time-series**
```sql
CREATE TABLE posts (
    id UUID, brand_id UUID,
    platform LowCardinality(String), platform_post_id String,
    author_handle String, author_follower_count UInt32,
    text String, media_urls Array(String),
    likes UInt32, shares UInt32, comments UInt32,
    permalink String,
    posted_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC') DEFAULT now64(),
    sentiment LowCardinality(String),
    cluster_id Nullable(UUID),
    source LowCardinality(String)
) ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (brand_id, platform, platform_post_id);

CREATE MATERIALIZED VIEW cluster_engagement_mv
ENGINE = SummingMergeTree
ORDER BY (brand_id, cluster_id)
AS SELECT brand_id, cluster_id, count() AS post_count,
       sum(likes) AS likes, sum(shares) AS shares, sum(comments) AS comments,
       max(author_follower_count) AS max_followers,
       countIf(sentiment = 'negative') AS neg_count
FROM posts WHERE cluster_id IS NOT NULL GROUP BY brand_id, cluster_id;
```

**Postgres + pgvector — transactional + vectors**
```sql
CREATE TABLE brands (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  vertical TEXT NOT NULL DEFAULT 'generic',
  voice_guidelines TEXT,
  keywords TEXT[] NOT NULL DEFAULT '{}',
  thresholds JSONB NOT NULL DEFAULT '{"critical":700,"high":400,"medium":200}',
  connections JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE severity_enum AS ENUM ('critical','high','medium','low');
CREATE TYPE cluster_status_enum AS ENUM ('active','resolved','snoozed');

CREATE TABLE clusters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id UUID NOT NULL REFERENCES brands(id),
  name TEXT, summary TEXT, centroid VECTOR(768),
  post_count INT NOT NULL DEFAULT 0,
  severity severity_enum NOT NULL DEFAULT 'low',
  severity_score FLOAT NOT NULL DEFAULT 0,
  tags TEXT[] NOT NULL DEFAULT '{}',
  sentiment_breakdown JSONB NOT NULL DEFAULT '{}',
  platforms TEXT[] NOT NULL DEFAULT '{}',
  first_seen_at TIMESTAMPTZ, last_activity_at TIMESTAMPTZ,
  status cluster_status_enum NOT NULL DEFAULT 'active',
  pinned_severity severity_enum
);

CREATE TABLE post_vectors (
  post_id UUID PRIMARY KEY,
  brand_id UUID NOT NULL REFERENCES brands(id),
  embedding VECTOR(768),
  cluster_id UUID REFERENCES clusters(id)
);
CREATE INDEX post_vectors_embedding_idx ON post_vectors USING hnsw (embedding vector_cosine_ops);
CREATE INDEX post_vectors_unclustered_idx ON post_vectors (brand_id) WHERE cluster_id IS NULL;

CREATE TYPE action_type_enum AS ENUM ('response','ticket','escalation','faq','insight','dm');
CREATE TYPE action_state_enum AS ENUM ('pending','approved','executed','rejected');

CREATE TABLE actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id UUID NOT NULL REFERENCES brands(id),
  type action_type_enum NOT NULL,
  state action_state_enum NOT NULL DEFAULT 'pending',
  cluster_id UUID NOT NULL REFERENCES clusters(id),
  target_post_id UUID,
  draft JSONB NOT NULL, context JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at TIMESTAMPTZ, decided_by UUID,
  reject_reason TEXT, outcome JSONB
);
CREATE INDEX actions_pending_idx ON actions (brand_id, created_at) WHERE state = 'pending';
```

## Backend

**Stack:** FastAPI 0.109+, Python 3.11+, ClickHouse Cloud, Postgres+pgvector (Supabase), Redis (Upstash), `google-genai`, `nimble-sdk`, `ddtrace`, `asyncpg`, `clickhouse-connect`, `httpx`, `arq`.

**Project Structure:**
```
backend/app/
├── main.py                  # FastAPI + ddtrace.patch_all()
├── config.py                # pydantic-settings
├── models.py                # Pydantic models
├── api/{webhooks,routes,websocket}.py
├── pipeline/{monitor,cluster,score,act}.py
├── adapters/{base,x,meta,nimble}.py
├── core/{ch,db,queue,llm,metrics,realtime}.py
├── destinations/{slack,jira,luminai}.py
└── workers/{pipeline_worker,cron}.py
```

**Key implementations** (full code in supporting docs / built during implementation):
- `core/ch.py` — async `clickhouse-connect` client; init `posts` + `cluster_engagement_mv` DDL.
- `core/llm.py` — `embed_batch`, `classify_sentiment` (1.5-flash, max_tokens 2), `summarize_cluster` (1.5-pro, JSON mode), `draft_response` (1.5-pro w/ brand voice).
- `core/metrics.py` — `span()` decorator over `ddtrace.tracer`; DogStatsD for counters/gauges/histograms incl. `pulse.latency.post_to_action_seconds`.
- `adapters/nimble.py` — `nimble_sdk.NimbleClient.search(sources=["reddit","tiktok","web"], structured=True, since_cursor)`.
- `destinations/luminai.py` — POST `/v1/workflows/classify` + `/v1/workflows/{id}/instances`. **De-identified summary only — never raw PHI.**
- `pipeline/monitor.py:persist_post` — insert ClickHouse row, classify inline, statsd increment, realtime publish, register `post_vectors` row, trigger `cluster.run` at 50 unclustered.
- `pipeline/cluster.py:run_clustering` — embed batch, pgvector NN, threshold-assign or create, `_merge_similar_clusters` at sim>0.88. Mirror cluster_id back to ClickHouse via `ALTER ... UPDATE`.
- `pipeline/score.py:run_scoring` — one ClickHouse aggregation per cluster from `cluster_engagement_mv` + live 2h velocity subquery; write `severity_score` + label; enqueue `act.run` if Critical.
- `pipeline/act.py:run_act` — top-N posts from ClickHouse, classify action type, generate draft. Healthcare brands → `luminai.classify_workflow` instead of generic ticketing.
- `workers/cron.py` — `poll_platforms()` (60s, Nimble), `refresh_engagement()` (15min, append new snapshots).

**Env vars:** `GEMINI_API_KEY`, `NIMBLE_API_KEY`, `CLICKHOUSE_HOST/PORT/USER/PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `DD_API_KEY`, `DD_SERVICE=pulse`, `LUMINAI_API_KEY`, `X_BEARER_TOKEN`, `X_WEBHOOK_SECRET`, `META_APP_SECRET`, `CLUSTER_SIMILARITY_THRESHOLD=0.82`, `MERGE_SIMILARITY_THRESHOLD=0.88`, `BATCH_SIZE=50`.

## Frontend

**Stack:** Next.js 14 App Router, TS, Tailwind, TanStack Query, Zustand, Recharts, Supabase Realtime client.

**Structure:**
```
frontend/
├── app/{layout,feed,clusters,queue,actions}/page.tsx
├── components/{PostCard,FeedSidebar,ClusterCard,QueueTable,
│   ActionCard,SeverityBadge,SentimentBar}.tsx
├── lib/{api,types,realtime}.ts
└── hooks/{useFeed,useClusters,useQueue,useActions,useRealtimeFeed}.ts
```

**Four views — one per pipeline stage:**
- **`/feed` (Monitor)** — PostCard list, platform filter pills, FeedSidebar with volume_24h + sentiment_7d sparkline (Recharts) + platform distribution. Realtime push via Supabase channel `feed:{brand_id}` invalidates the query.
- **`/clusters` (Cluster)** — card grid sorted by severity. SeverityBadge + SentimentBar + tag chips per card.
- **`/queue` (Score)** — table with explicit `volume / engagement / sentiment / velocity / influence` columns; SeverityBadge at end.
- **`/actions` (Act)** — ActionCard with editable textarea for response drafts, `Approve / Edit & Approve / Reject` mutation buttons. TanStack invalidate on success.

**Aesthetic:** Indigo primary, sentiment color-coded left-border on PostCard (green/red/gray/blue), severity badges (red/orange/yellow/gray). MVP can poll @30s and upgrade to Supabase Realtime in v1.0.

## Demo Prep

**Seed script** (`scripts/seed_demo.py`) — creates "Acme Coffee" (generic) or healthcare brand, inserts ~10 staged "checkout crash" posts across X and Reddit with negative sentiment + viral engagement, runs `run_clustering` and `run_scoring`. Result: one Critical cluster + drafted response and ticket awaiting approval on stage.

**Demo Script (3 minutes):**
- 0:00 — "Pulse listens to 5 platforms, clusters into themes, ranks by business severity, drafts the response."
- 0:30 — Live Feed streams posts; filter to X; inject staged crash posts via seed.
- 1:00 — Clusters view: "App Checkout Crash (v4.2.1)" climbs to Critical.
- 1:30 — Priority Queue: show breakdown columns (volume/engagement/sentiment/velocity/influence).
- 2:00 — Actions: drafted on-brand 280-char response + P1 ticket. Approve in one click.
- 2:30 — "Nimble feeds it · Gemini reasons · ClickHouse aggregates · Datadog watches · Luminai routes for health systems."
- 2:50 — Close: $60/mo COGS, ~80% margin at $299, healthcare vertical via Luminai.

**Backup plans:**
- Live ingest fails → run seed script (deterministic Critical).
- Gemini rate-limit → fall back drafting to 1.5-flash; pre-cache demo cluster summary.
- Nimble slow → X webhook + seed cover.
- Realtime down → 30s polling fallback.
- ClickHouse unreachable → Postgres count fallback for scoring.

## Performance Notes

- Batch embeddings up to 100/call.
- `cluster_engagement_mv` SummingMergeTree → scoring reads one row.
- `post_vectors_unclustered_idx` partial index → O(1) batch-trigger count.
- pgvector HNSW → sub-ms nearest-neighbor.
- asyncpg pool min 5 / max 20.
- Datadog spans identify the bottleneck (usually Gemini drafting); scale that worker.

## Success Criteria

**Must Have:** X webhook → ClickHouse → cluster → score → action drafts → approval workflow → deployed URL.
**Should Have:** All 4 views, Nimble open-web source, Datadog dashboard, full score-breakdown columns, pre-seeded incident.
**Nice to Have:** Datadog post-to-action <2 min SLO green on stage, Luminai healthcare routing, time-decay re-ranking demo, sparkline + platform distribution, influence multiplier visibly boosting a creator complaint.

## Cost @ 1K posts/day

| Component | Monthly |
|---|---|
| 🧠 Gemini (embed + classify + summarize + draft) | ~$3.64 |
| 🔍 Nimble | ~$12 |
| 🏠 ClickHouse Cloud (dev) | ~$20 |
| Supabase Pro | ~$25 |
| Upstash Redis | ~$5 |
| Render web + worker | ~$20 |
| 🐶 Datadog (1 host) | ~$31 |
| **Total** | **~$142/mo** |

$349/mo SaaS → ~60% gross margin. Luminai priced separately as healthcare add-on.

---

**Document Version:** 1.0 (auto-approved 2026-05-23)
**Status:** Ready for Implementation

---

# Addendum: LLMO (LLM Optimization) as First-Class Subsystem

> **Added 2026-05-23 per user direction:** "Search for llmo stuff fully and incorporate llmo into key framework of what we r doing. And then i need u to, on the main page when u give an overall score, give social media subscore and llmo subscore."

## A.1 Why LLMO

LLMO (Large Language Model Optimization, also called Generative Engine Optimization / GEO) is the discipline of tracking and shaping how AI models — ChatGPT, Claude, Gemini, Perplexity — describe, cite, and contextualize a brand. **Per industry research (Gartner / Searchengineland / Frase 2026):**

- **58% of online searches involve an AI-generated answer or summary** (mid-2025).
- LLMO targets **mention probability and citation accuracy**, not ranking position.
- **Cross-platform variance is enormous** — ChatGPT and Perplexity agree on the top recommended brand only 60-80% of the time → must surface per-LLM breakdown.
- **Detection rigor:** multi-model consensus (≥3 LLMs citing same work) yields 95.6% accuracy; within-prompt repetition (≥2 replications) yields 88.9%. Run each probe prompt 3-5× per LLM for stability.

Legacy social-listening tools (Brandwatch, Sprout, Mention) don't do this at all. LLMO is the 2026 wedge.

## A.2 LLMO Pipeline (parallel to Monitor → Cluster → Score → Act)

```
            ┌─→ Monitor (social) → Cluster → Score (social_score) ─┐
            │                                                       │
Brand ──────┤                                                       ├─→ Overall Score
            │                                                       │
            └─→ LLM Probe       → Audit Store → LLMO Score ────────┘
                                                       │
                                                       └─→ Act (ground-truth correction, prompt-content fill)
```

### Stage L — LLM Probe (new, runs on a cron — every 15 min during demo)

1. Load `brand_prompts` for the brand (10-20 synthetic queries a buyer would actually ask: *"best AI law firm for startups"*, *"alternatives to Harvey AI"*, etc.).
2. For each prompt × each LLM (Claude, ChatGPT, Gemini, Perplexity), run the prompt **3 times** (within-prompt repetition for stability).
3. Implementation: **Gemini-with-system-prompt-impersonation** for all 4 (faster, free-tier-friendly, deterministic). The system prompt tells the model to respond as if it were Claude/ChatGPT/Gemini/Perplexity, honoring known training-cutoff + style differences. Real provider APIs are an upgrade path post-MVP.
4. For each response, extract:
   - `mentioned: bool` — does the response mention the brand
   - `position: int` — 1 = headline/first sentence, 2 = early body, 3 = later body, 4 = list item, 0 = absent
   - `competitors_mentioned: string[]` — known competitor names from a per-brand list
   - `sentiment: float` (−1..+1) — how the brand is positioned
   - `claims: string[]` — factual claims about the brand
   - `drift_score: float` (0..1) — Gemini scores each claim against the brand's `ground_truth` doc; aggregate = drift score
5. Write to ClickHouse `llmo_audits` (append-only). Trigger LLMO score recompute.

## A.3 LLMO Score (0-100)

```
LLMO Score = 0.30·CitationFrequency + 0.25·ShareOfVoice + 0.25·CitationAccuracy + 0.20·SentimentQuality
```

| Component | Formula |
|---|---|
| **CitationFrequency** | `Σ position_weight(audit) / total_probes · 100`, where `position_weight = {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.2, 0: 0}` |
| **ShareOfVoice** | `brand_mentions / (brand_mentions + Σ competitor_mentions) · 100` across all probes |
| **CitationAccuracy** | `avg(100 · (1 − drift_score))` across audits where `mentioned=true` |
| **SentimentQuality** | `avg sentiment in [-1..1]` → linearly rescaled to `[0..100]` |

### Per-LLM grid (must render on main page)

Each LLM gets its own card showing: LLMO score, citation frequency, drift indicator, last 24h trend sparkline. This surfaces the cross-platform variance directly — "you score 87 in Claude but 61 in ChatGPT, and the drift is here."

## A.4 Overall Brand Health (the main page hero)

```
Overall Brand Health = 0.50·SocialScore + 0.50·LLMOScore
```

`SocialScore` is the brand-aggregate roll-up of the existing severity model:
```
SocialScore = 100 − clamp(weighted_severity_pressure_24h, 0, 100)
weighted_severity_pressure_24h = Σ(critical_clusters × 30 + high × 15 + medium × 5)
```

Higher SocialScore = healthier (fewer critical clusters in the last 24h). Pulse's existing per-cluster `severity_score` is unchanged; the brand-level `SocialScore` is a *new* roll-up that lives on `pulse_scores` snapshots.

The main-page hero shows **3 big numbers side by side**:
- **OVERALL** (composite, 0-100, large central number)
- **SOCIAL** (subscore + delta vs 24h + sparkline)
- **LLMO** (subscore + delta vs 24h + sparkline)

## A.5 New data model

### TypeScript additions

```typescript
export interface LLMAudit {
  id: string;
  brand_id: string;
  llm: "claude" | "chatgpt" | "gemini" | "perplexity";
  prompt: string;
  prompt_id: string;
  response: string;
  mentioned: boolean;
  position: 0 | 1 | 2 | 3 | 4;
  competitors_mentioned: string[];
  sentiment: number;          // -1..+1
  claims: string[];
  drift_score: number;        // 0..1
  citation_accuracy: number;  // 0..100
  ingested_at: string;
}

export interface BrandPrompt {
  id: string;
  brand_id: string;
  prompt: string;
  intent: string;             // "comparison" | "discovery" | "alternative" | "research"
}

export interface ScoreSnapshot {
  brand_id: string;
  timestamp: string;
  overall: number;
  social: number;
  llmo: number;
  social_breakdown: {
    critical_clusters: number;
    high_clusters: number;
    medium_clusters: number;
    volume_24h: number;
    negative_pct: number;
  };
  llmo_breakdown: {
    citation_frequency: number;
    share_of_voice: number;
    citation_accuracy: number;
    sentiment_quality: number;
    per_llm: Record<"claude"|"chatgpt"|"gemini"|"perplexity", {
      score: number;
      mention_rate: number;
      avg_position: number;
      drift: "low" | "medium" | "high";
    }>;
  };
}
```

### ClickHouse — `llmo_audits` (new)

```sql
CREATE TABLE IF NOT EXISTS llmo_audits (
    id                    UUID,
    brand_id              UUID,
    llm                   LowCardinality(String),
    prompt                String,
    prompt_id             UUID,
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
```

### Postgres additions

```sql
ALTER TABLE brands ADD COLUMN IF NOT EXISTS ground_truth TEXT;
ALTER TABLE brands ADD COLUMN IF NOT EXISTS competitors TEXT[] NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS brand_prompts (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id  UUID NOT NULL REFERENCES brands(id),
    prompt    TEXT NOT NULL,
    intent    TEXT NOT NULL DEFAULT 'discovery'
);
```

## A.6 New API endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/api/scores?brand_id=` | Current `ScoreSnapshot` + 24h sparklines for overall/social/llmo |
| GET | `/api/llmo/audits?brand_id=&llm=` | Recent LLMAudits (paged), filterable by LLM |
| POST | `/api/llmo/probe?brand_id=` | Manually trigger one LLM probe iteration (used by the demo's "tick now" button) |
| GET | `/api/brands/{id}/prompts` · POST | Brand-prompts CRUD |

## A.7 Frontend addition — `/dashboard` (the main page, default redirect)

Replaces `/feed` as the default landing page. Top section: 3-number hero (Overall/Social/LLMO). Below: per-LLM grid for LLMO + critical anomalies + recent activity. Updated nav:

```
Pulse  |  Dashboard  ·  Live Feed  ·  Clusters  ·  Priority Queue  ·  LLMO  ·  Actions
```

New components:
- `<ScoreHero />` — three big numbers side-by-side with sparklines + deltas
- `<LLMVisibilityGrid />` — 4 cards, one per LLM, with score / mention rate / drift indicator
- `<PromptResults />` — drill-down: per-prompt × per-LLM matrix showing where the brand appeared
- `<GroundTruthDriftCard />` — currently-detected drift event with side-by-side ground truth vs LLM claim + drafted correction (lives in Actions queue as `ground_truth_correction` action type — same approval workflow)

## A.8 Action type addition

`ground_truth_correction` joins the existing 6 action types. Triggered when `drift_score > 0.4` on any LLM. Draft is generated by Gemini using the brand's `ground_truth` doc. Routed through the same `Pending → Approved → Executed` workflow; on execution, Pulse posts the correction to the brand's Slack `#brand-corrections` channel (and in future, files a structured correction with the LLM provider where supported).

## A.9 Demo narrative update

The original Acme Coffee social-only demo still works. **Better demo flow (recommended)** auditing a real brand (Crosby or any sponsor) and showing the LLMO drift event in front of judges:

1. 0:00 — Dashboard: Overall 73 / Social 81 / LLMO 65 (LLMO visibly lower). The story already lives in the numbers.
2. 0:30 — Live Feed: social posts streaming.
3. 0:50 — LLMO view: ChatGPT card pulses, citation accuracy drops, "DRIFT DETECTED" badge appears.
4. 1:10 — Side-by-side: ground truth vs ChatGPT's description.
5. 1:30 — Actions queue: drafted `ground_truth_correction` waiting for approval — and a regular `response` action for a social cluster underneath.
6. 1:50 — Approve correction → Slack post lands.
7. 2:10 — Close: "Pulse fuses social listening with LLMO — what your customers say *and* what the AIs say about you, on one composite Brand Health score."

## A.10 LLMO worktree ownership

`lib/llmo/*`, `app/pipeline/llmo.py`, `app/pipeline/llmo_scoring.py`, `app/api/llmo_routes.py`, and the `llmo_audits` migration belong to **Track 1 (Engine)**. The `<ScoreHero />`, `<LLMVisibilityGrid />`, `<PromptResults />`, `<GroundTruthDriftCard />` components and the `/dashboard` + `/llmo` pages belong to **Track 3 (Frontend)**. The `/api/scores`, `/api/llmo/*`, and `/api/brands/.../prompts` routes belong to **Track 2 (Surface)**.

