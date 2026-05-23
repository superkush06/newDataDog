# Track 2 Incomplete Dependencies

This file documents the parts of the Track 2 surface that are intentionally not fully implemented yet because the matching Track 1 engine/core modules, runtime services, or packaging setup are not present in this worktree.

The current implementation prioritizes import cleanliness, stable API shapes, safe no-key/no-service behavior, and unit-testable boundaries. The placeholders should be replaced during integration after Track 1 lands.

## Environment / Packaging

- `python` is not available in this shell; checks were run with `python3`.
- `pip install -e ".[dev]"` does not currently work because setuptools discovers both `app` and `migrations` as top-level packages in `backend/`.
- Integration fix needed: update `backend/pyproject.toml` with explicit package discovery, for example include only `app*` and exclude `migrations*`.
- Some dependencies are globally available enough for tests/import checks, but a proper virtualenv install is still needed for a repeatable backend environment.

## Missing Track 1 Core Modules

These imports are not present in this worktree and are guarded defensively:

- `app.core.db`
- `app.core.ch`
- `app.core.queue`
- `app.core.realtime`

Impact:

- DB-backed REST endpoints return stable placeholder responses when `app.core.db.pool` is absent.
- ClickHouse-backed endpoints return stable placeholder responses when `app.core.ch.ch` is absent.
- Webhooks and LLMO probe endpoints return skipped queue results when `app.core.queue.enqueue` is absent.
- WebSocket connections still accept and send a placeholder status when `app.core.realtime` is absent.

Integration needed:

- Provide async Postgres pool initialization and `pool.acquire()`.
- Provide ClickHouse client helper `ch()`.
- Provide queue helper `enqueue(job_name, payload)`.
- Provide realtime helpers `subscribe(brand_id, websocket)` and `unsubscribe(brand_id, websocket)`.

## API Routes With Placeholder Behavior

### `backend/app/api/routes.py`

Implemented endpoints:

- `GET /api/health`
- `GET /api/feed`
- `GET /api/clusters`
- `GET /api/queue`
- `GET /api/actions`
- `POST /api/actions/{action_id}`
- `POST /api/brands`
- `PATCH /api/brands/{brand_id}`

Incomplete until Track 1/core services land:

- `/api/feed` needs real ClickHouse reads from `posts`.
- `/api/clusters`, `/api/queue`, `/api/actions`, `/api/brands` need real Postgres access.
- `/api/queue` currently has no real score breakdown because Track 1 scoring helpers/stores are not present.
- `PATCH /api/brands/{brand_id}` returns placeholder/501-style behavior until DB-backed partial update is wired.

### `backend/app/api/scores_route.py`

Implemented endpoint:

- `GET /api/scores`

Incomplete until Track 1 lands:

- Uses placeholder scores when `app.core.db.pool` is missing.
- Attempts to call `app.pipeline.brand_scoring.recompute` only if it exists.
- Needs Track 1 brand-level scoring implementation and `pulse_scores` data.

### `backend/app/api/llmo_routes.py`

Implemented endpoints:

- `GET /api/llmo/audits`
- `POST /api/llmo/probe`
- `GET /api/brands/{brand_id}/prompts`
- `POST /api/brands/{brand_id}/prompts`

Incomplete until Track 1/core services land:

- `/api/llmo/audits` needs ClickHouse `llmo_audits` access.
- `/api/llmo/probe` needs queue access and Track 1 `app.pipeline.llmo.run_probe`.
- Prompt endpoints need Postgres `brand_prompts` access.

## Worker / Cron Placeholders

### `backend/app/workers/pipeline_worker.py`

Worker function surfaces exist:

- `monitor_persist`
- `cluster_run`
- `score_run`
- `act_run`
- `llmo_probe`
- `score_recompute`
- `draft_correction`

Incomplete until Track 1 lands:

- `monitor_persist` needs `app.pipeline.monitor.persist_post`.
- `cluster_run` needs `app.pipeline.cluster.run_clustering`.
- `score_run` needs `app.pipeline.score.run_scoring`.
- `act_run` needs `app.pipeline.act.run_act`.
- `llmo_probe` needs `app.pipeline.llmo.run_probe`.
- `score_recompute` needs `app.pipeline.brand_scoring.recompute`.
- `draft_correction` needs `app.pipeline.act.run_correction`.

Current behavior:

- Missing dependencies return a clear skipped result instead of failing import.

### `backend/app/workers/cron.py`

Cron entrypoints exist:

- `poll_platforms`
- `refresh_engagement`
- `run_llmo_probes`

Incomplete until Track 1/core services land:

- `poll_platforms` needs brand reads from Postgres and Nimble polling persistence.
- `refresh_engagement` needs platform engagement refresh logic and ClickHouse/queue access.
- `run_llmo_probes` needs brand id discovery from Postgres and queue access.

## Webhook Queue Integration

### `backend/app/api/webhooks.py`

Implemented:

- HMAC verification.
- Adapter lookup.
- Payload normalization.
- Queue wrapper with safe skipped result.

Incomplete until Track 1 lands:

- Real enqueue requires `app.core.queue.enqueue`.
- Real downstream persistence requires Track 1 Monitor stage.

Tests cover:

- Valid signature.
- Invalid signature rejection.
- Normalized payload path.
- Missing queue behavior.

## Destinations

### `backend/app/destinations/slack.py`

Implemented:

- Posts to Slack webhook if provided.
- Returns skipped result if webhook URL is missing.

Incomplete:

- No retry/backoff policy yet.
- No higher-level action execution orchestration until Track 1 Act stage exists.

### `backend/app/destinations/luminai.py`

Implemented:

- Calls workflow classify/execute endpoints if API key is configured.
- Returns skipped result when API key or workflow id is missing.

Incomplete:

- Real workflow ids/payload contracts need to be validated against Luminai production API.
- No retry/backoff policy yet.
- No healthcare ticket routing until Track 1 Act stage wires it.

## Seed Scripts

### `backend/scripts/seed_demo.py`

Implemented:

- Safe script shape for Acme Coffee demo data.
- Cleanly skips if `asyncpg` or `DATABASE_URL` is missing.

Incomplete:

- Does not seed ClickHouse posts yet.
- Requires real Postgres schema and DB connection.
- Should be expanded after Track 1 storage helpers are available.

### `backend/scripts/seed_llmo.py`

Implemented:

- Safe script shape for Crosby and Acme LLMO ground truth/prompts.
- Cleanly skips if `asyncpg` or `DATABASE_URL` is missing.

Incomplete:

- Requires real Postgres schema and DB connection.
- Should be validated after migrations are applied.

## Migrations

Added:

- `backend/migrations/003_llmo.sql`
- `backend/migrations/004_postgres_llmo.sql`

Updated:

- `backend/scripts/apply_migrations.py`

Incomplete:

- Migration runner compiles, but real execution was not run because ClickHouse/Postgres env and dependencies are not configured here.
- ClickHouse/Postgres migration ordering should be verified against the deployment environment.

## Tests / Verification Status

Passing:

- `pytest backend/tests/test_adapters.py backend/tests/test_webhooks.py -v`
- `python3 -c "from app.main import app; print(app.title)"`
- `python3 -m py_compile backend/scripts/apply_migrations.py`

Not fully verified:

- Real DB queries.
- Real ClickHouse reads/writes.
- Real Redis/arq enqueue.
- Real websocket pub/sub.
- Real Slack/Luminai network calls.
- Real migrations against live services.

## Integration Checklist

1. Fix `backend/pyproject.toml` package discovery so `pip install -e ".[dev]"` works.
2. Merge Track 1 core modules: DB, ClickHouse, queue, realtime, metrics.
3. Merge Track 1 pipeline modules: monitor, cluster, score, act, llmo, brand_scoring.
4. Replace placeholder responses with real store-backed paths where guarded imports currently skip.
5. Apply migrations to ClickHouse and Postgres.
6. Run API smoke tests against configured services.
7. Add integration tests for queue, DB, ClickHouse, and action execution.
