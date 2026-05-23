# CLAUDE.md — Pulse Project State

> Hand-off after context clear. Read this top-to-bottom before any tool call.

## Project

**Pulse** — social listening + LLMO (LLM Optimization) brand-health agent for the Autonomous Agents Hackathon 2026. Monitor → Cluster → Score → Act pipeline with a parallel LLM Probe (LLMO) subsystem that audits how Claude/ChatGPT/Gemini/Perplexity describe a brand vs ground truth.

- Repo: https://github.com/superkush06/newDataDog
- Local: `/Users/kushagrabehl/Downloads/newData/newDataDog`
- Demo target: Crosby (crosby.ai) — AI-first law firm
- User: kush@slashy.com (superkush06)

## Stack

- **Backend:** FastAPI + asyncpg + clickhouse-connect (>=0.8.0, async) + arq Redis + Groq + local sentence-transformers + Datadog + ddtrace
- **Frontend:** Next.js 14 App Router + TS + Tailwind + TanStack Query + recharts
- **LLM:** Groq (`llama-3.1-8b-instant` for sentiment/judge, `llama-3.3-70b-versatile` for drafting/cluster summary/4-LLM impersonation). NOT Gemini.
- **Embeddings:** local `sentence-transformers/all-MiniLM-L6-v2` (384-dim) — no API.
- **Sponsors integrated:** Nimble, Groq (was Gemini track), ClickHouse, Datadog, Luminai (healthcare v2)

## Repo Layout

```
newDataDog/
├── .env                     ← global env, single source of truth (gitignored)
├── .env.example             ← committed template
├── CLAUDE.md                ← this file
├── docs/superpowers/
│   ├── specs/               2026-05-23-pulse-design.md (auth spec + LLMO addendum)
│   ├── plans/               2026-05-23-pulse-implementation.md (43 tasks)
│   └── handoffs/            track-1, track-2, track-3, integrator, track-2-incomplete-dependencies
├── backend/
│   ├── pyproject.toml       deps + setuptools.packages config
│   ├── app/
│   │   ├── config.py        pydantic-settings, reads ../.env via Path(__file__).parents[2]/.env
│   │   ├── models.py        Pydantic mirror of spec
│   │   ├── core/            ch.py db.py queue.py llm.py metrics.py realtime.py
│   │   ├── pipeline/        monitor cluster score act llmo llmo_scoring brand_scoring score_formula
│   │   ├── api/             webhooks routes scores_route llmo_routes websocket
│   │   ├── adapters/        base x meta nimble
│   │   ├── destinations/    slack luminai
│   │   ├── workers/         pipeline_worker cron
│   │   └── main.py
│   ├── migrations/          001_clickhouse 002_postgres 003_llmo 004_postgres_llmo
│   ├── scripts/             apply_migrations.py · verify_env.py · seed_demo.py · seed_llmo.py
│   ├── tests/               test_adapters test_webhooks test_scoring test_llmo_scoring test_llm_prompts
│   └── .venv/               ← installed (groq, sentence-transformers, aiohttp, all deps)
└── frontend/
    ├── app/                 dashboard/ feed/ clusters/ queue/ llmo/ actions/
    ├── components/          ScoreHero LLMVisibilityGrid PromptResults GroundTruthDriftCard ...
    ├── hooks/               useFeed useClusters useQueue useActions useScores useLLMOAudits useRealtimeFeed
    ├── lib/                 api.ts types.ts realtime.ts
    └── mock-server.mjs      dev-only fallback before backend is up
```

## Git State (as of last session)

- Branch: `main` at HEAD `e763e2c` (merge of track-3-frontend)
- All three tracks (`track-1-engine`, `track-2-surface`, `track-3-frontend`) are already merged into `main`. Don't re-merge.
- Worktrees at `../pulse-worktrees/{track-1-engine,track-2-surface,track-3-frontend}` still exist on disk but are no longer needed.
- All branches pushed to origin.

## What WORKS Right Now

- Backend imports cleanly. `pyproject.toml` has explicit `[tool.setuptools] packages = [...]` + `clickhouse-connect>=0.8.0` + `pytest>=8.0.0` + `pytest-asyncio>=0.25.0` + `aiohttp` runtime-added for CH async.
- 10/10 backend pure-function tests pass (`pytest tests/test_scoring.py tests/test_llmo_scoring.py tests/test_llm_prompts.py`)
- `verify_env.py` reaches:
  - ✓ **Groq** (key works, llama-3.1-8b returns "Okay")
  - ✓ **Embedder** (local MiniLM-L6 loads, returns 384-dim vector)
  - ✓ **Nimble** (HTTP 404 on /v1/health — endpoint may not exist but auth header reached server)

## What's BLOCKED — User Must Fix in `.env`

The user said "I filled in the env" but **3 of the values are wrong format** and these still need their hands:

### 1. Postgres `DATABASE_URL` is broken

Current value: `postgresql://postgres:8Bl69Omt6yX76z4c@db.eniywubmjokiuiaswhin.supabase.co:5432/postgres`

`db.<project>.supabase.co` **does NOT resolve anymore.** Supabase moved direct connections behind the pooler.

**Fix:** Supabase Dashboard → Project (`eniywubmjokiuiaswhin`) → Settings → Database → Connection String → URI tab → **Session pooler** radio → copy that URL. Should look like:
```
postgresql://postgres.eniywubmjokiuiaswhin:8Bl69Omt6yX76z4c@aws-0-<region>.pooler.supabase.com:5432/postgres
```
Use **port 5432 (session pooler)**, NOT 6543 (transaction pooler — asyncpg breaks on prepared statements).

### 2. Redis `REDIS_URL` is using the wrong password

Current value: `rediss://default:gQAAAAAAAg7hAAIgcDI1NWMwYWNlNWIyOWM0MzRiOGFhNTQwYjRkNzE2OWRhYQ@wanted-baboon-134881.upstash.io:6379`

The `gQAA...` token is the **Upstash REST API token**, NOT the Redis-protocol password. They are different. TCP to the host on 6379 succeeds, just auth fails.

**Fix:** Upstash console → `wanted-baboon-134881` DB → "TCP" tab (or "Connect" → "Redis CLI") → copy the **Redis password** (different from REST token). Or just copy the whole `rediss://default:<PWD>@<host>:6379` connection string they show.

### 3. ClickHouse `CLICKHOUSE_HOST` works but service idles

Current value: `fijdzrvb1r.us-east1.gcp.clickhouse.cloud` (correct, plain host — no `https://` or port). DNS resolves, TCP 8443 is reachable. The Python client got "Cannot connect" because ClickHouse Cloud free tier **auto-idles after ~15 min**.

**Fix:** ClickHouse Cloud dashboard → service → wake / un-idle (takes ~30s on first connection). Then re-run verify.

### Verify command (after fixes)

```bash
cd /Users/kushagrabehl/Downloads/newData/newDataDog/backend
.venv/bin/python scripts/verify_env.py
```

All 5 REQUIRED checks (Groq, Embedder, ClickHouse, Postgres, Redis) should turn green.

## Next Tasks (in order)

1. **Re-run `verify_env.py`** — confirm all 5 required services green.
2. **Apply migrations**:
   ```bash
   .venv/bin/python scripts/apply_migrations.py
   ```
   This applies `001_clickhouse.sql` + `003_llmo.sql` to ClickHouse, and `002_postgres.sql` + `004_postgres_llmo.sql` to Postgres (creates pgvector extension, brands, clusters, post_vectors, actions, brand_prompts, pulse_scores).
3. **Seed demo data**:
   ```bash
   .venv/bin/python scripts/seed_demo.py        # Acme Coffee + Critical checkout-crash cluster
   .venv/bin/python scripts/seed_llmo.py crosby # Crosby ground truth + brand_prompts + competitors
   ```
   Copy the printed `brand_id` into `.env` as `NEXT_PUBLIC_DEMO_BRAND_ID=<uuid>`.
4. **Start services**:
   ```bash
   # terminal 1
   cd backend && .venv/bin/uvicorn app.main:app --reload
   # terminal 2
   cd backend && .venv/bin/arq app.workers.pipeline_worker.WorkerSettings
   # terminal 3
   cd frontend && npm install && npm run dev
   ```
5. **Smoke test the dashboard**: open http://localhost:3000 — should land on `/dashboard` with Overall/Social/LLMO scores. Click "Run LLM Probe" — should populate `/llmo` view within ~30s with 4-LLM grid.
6. **End-to-end test plan** (Task 33 in plan doc):
   - `curl http://localhost:8000/api/health` → ClickHouse + Postgres both "connected"
   - `curl "http://localhost:8000/api/scores?brand_id=<UUID>"` → overall+social+llmo numbers
   - `curl -X POST "http://localhost:8000/api/llmo/probe?brand_id=<UUID>"` → 202 + worker should process within ~30s
   - Visit `/actions` → seeded response + ticket actions visible, "Approve" button transitions state

## Critical Gotchas

- **pyproject.toml** must have `[tool.setuptools] packages = ["app", "app.api", "app.adapters", "app.core", "app.pipeline", "app.destinations", "app.workers"]` — without it, setuptools chokes on the `migrations/` sibling dir.
- **CLAUDE.md at `/Users/kushagrabehl/Downloads/CLAUDE.md`** is for an unrelated project ("Epoch"). Ignore it. This file at `/Users/kushagrabehl/Downloads/newData/newDataDog/CLAUDE.md` is the source of truth.
- **DO NOT swap back to Gemini.** User explicitly chose Groq for free-tier headroom. The 4-LLM impersonation in `pipeline/llmo.py` uses Groq llama-3.3 with model-specific system prompts (Claude/ChatGPT/Gemini/Perplexity voices). Real provider APIs are post-MVP swap.
- **Embeddings are LOCAL** (sentence-transformers/all-MiniLM-L6-v2 → 384-dim). Migrations use `VECTOR(384)`. Don't change to 768.
- **The user does not have Docker.** Redis is on Upstash. ClickHouse is on ClickHouse Cloud. Postgres is on Supabase. All hosted.
- **`db.<project>.supabase.co` is dead** — always use the pooler hostname `aws-0-<region>.pooler.supabase.com`.
- **Upstash REST token ≠ Redis password** — common mistake.
- The user uses heavy hooks that inject system-reminders about Lumen and Foundry. Ignore both unless directly relevant.
- The user is in a rush (hackathon). Don't ask permission for installs/migrations — just do them.

## File Cheat-Sheet

| Need to... | Open... |
|---|---|
| Re-read the design | `docs/superpowers/specs/2026-05-23-pulse-design.md` |
| Look up a task | `docs/superpowers/plans/2026-05-23-pulse-implementation.md` (43 tasks) |
| See the LLMO logic | `backend/app/pipeline/llmo.py` + `llmo_scoring.py` + `brand_scoring.py` |
| Fix an API route | `backend/app/api/{webhooks,routes,scores_route,llmo_routes,websocket}.py` |
| Frontend hero | `frontend/components/ScoreHero.tsx` + `frontend/app/dashboard/page.tsx` |
| Per-LLM grid | `frontend/components/LLMVisibilityGrid.tsx` + `frontend/app/llmo/page.tsx` |

## Recent Commits (newest first)

```
e763e2c Merge remote-tracking branch 'origin/track-3-frontend'
01dfee2 feat(frontend): complete Track 3 — Next.js dashboard + all views
093261a refactor(llm): swap Gemini→Groq + local sentence-transformers
83e7d1e feat: add track 2 backend surface
09e36be feat(pipeline): Monitor → Cluster → Score → Act + LLMO
44909d0 feat(core): infrastructure clients (CH, PG, queue, Datadog, Gemini→Groq, realtime)
818dcbe refactor(env): swap Gemini→Groq references in verify_env.py
72a447e refactor(env): single global .env at repo root
```

---

**TL;DR for next session:** Read this file. User has filled in `.env` but 3 values are wrong format. Tell them exactly what to fix (see "What's BLOCKED" above), then once they say "go", run verify → migrate → seed → start services → smoke-test.
