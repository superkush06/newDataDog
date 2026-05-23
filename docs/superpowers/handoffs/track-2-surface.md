# Track 2 — Surface (adapters + API + workers + destinations)

**Branch:** `track-2-surface`
**Worktree path:** `../pulse-worktrees/track-2-surface`
**Owner files:** `backend/app/adapters/*`, `backend/app/api/*`, `backend/app/workers/*`, `backend/app/destinations/*`, `backend/app/main.py`, `backend/scripts/seed_demo.py`, `backend/scripts/seed_llmo.py`, `backend/migrations/003_llmo.sql`, `backend/migrations/004_postgres_llmo.sql`

## Your scope

You build the **surface** — HTTP routes, platform adapters, the arq worker, the cron, destination clients (Slack, Luminai). Plus the LLMO migrations and prompt seeds.

## Read first

- Spec: `docs/superpowers/specs/2026-05-23-pulse-design.md` (especially §4 API Contract, §A.6 LLMO routes)
- Plan: `docs/superpowers/plans/2026-05-23-pulse-implementation.md`

## Your tasks (in order)

| # | Task | File(s) |
|---|---|---|
| 13 | Adapter base + X normalizer (+ tests) | `app/adapters/{base,x,__init__}.py` + `tests/test_adapters.py` |
| 14 | Meta + Nimble normalizers | `app/adapters/{meta,nimble}.py` |
| 19 | Slack + Luminai destinations | `app/destinations/{slack,luminai}.py` |
| 21 | Webhook routes (HMAC) | `app/api/webhooks.py` + `tests/test_webhooks.py` |
| 22 | REST routes (feed/clusters/queue/actions/brands/health) | `app/api/routes.py` |
| 23 | WebSocket route + `main.py` | `app/api/websocket.py` + `app/main.py` |
| 24 | arq pipeline worker + cron | `app/workers/{pipeline_worker,cron}.py` |
| 25 | Acme seed (social Critical cluster) | `scripts/seed_demo.py` |
| 34 | **LLMO migrations (003 + 004)** | `migrations/003_llmo.sql`, `migrations/004_postgres_llmo.sql` |
| 38 | **`/api/scores` + `/api/llmo/*` routes** | `app/api/{scores_route,llmo_routes}.py` + `main.py` + `workers/pipeline_worker.py` |
| 39 | **LLMO probe cron + Crosby/Acme prompt seed** | `app/workers/cron.py` + `scripts/seed_llmo.py` |
| 40 | **`ground_truth_correction` action type** | `app/pipeline/act.py` (small append) + `pipeline_worker.py` |

## Setup

```bash
cd ../pulse-worktrees/track-2-surface/backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Allowed imports

You may import from `app.config`, `app.models`, your own files, **and** Track 1's pipeline/core modules — but you'll have to stub them when developing solo since Track 1's branch hasn't merged yet. Pattern for stub imports:

```python
# top of your file, when the real module isn't there yet:
try:
    from app.pipeline.monitor import persist_post
except ImportError:
    async def persist_post(*a, **k): return "stub-id"  # remove after merge
```

For Task 40 (which extends `app/pipeline/act.py`), coordinate with the integrator — either Track 1 includes a hook for it, or you append after merge.

## Verification

```bash
pytest tests/test_adapters.py tests/test_webhooks.py -v
uvicorn app.main:app --port 8001 &
curl -s http://localhost:8001/api/health
kill %1
```

The health endpoint will report DB connection errors when Track 1's clients aren't fully wired — that's expected pre-merge.

## Hand-back

Push `track-2-surface`. Integrator merges after Track 1.
