# Track 1 — Engine (backend core + pipeline + LLMO)

**Branch:** `track-1-engine`
**Worktree path:** `../pulse-worktrees/track-1-engine`
**Owner files:** `backend/app/core/*`, `backend/app/pipeline/*`, the LLMO pipeline + scoring + brand rollup

## Your scope

You build the **engine** — the deterministic core of Pulse. No HTTP, no UI. Pure async functions plus the integration adapters for ClickHouse, Postgres, Redis, Datadog, Gemini.

## Read first

- Spec: `docs/superpowers/specs/2026-05-23-pulse-design.md` (especially §3 Pipeline, §A LLMO Addendum)
- Plan: `docs/superpowers/plans/2026-05-23-pulse-implementation.md` (your tasks below)

## Your tasks (in order)

| # | Task | File(s) | TDD? |
|---|---|---|---|
| 7  | ClickHouse client singleton | `app/core/ch.py` | no |
| 8  | Postgres asyncpg pool | `app/core/db.py` | no |
| 9  | Redis arq queue wrapper | `app/core/queue.py` | no |
| 10 | Datadog metrics + spans | `app/core/metrics.py` | no |
| 11 | Gemini LLM wrappers | `app/core/llm.py` + `tests/test_llm_prompts.py` | yes |
| 12 | Realtime WS pub/sub | `app/core/realtime.py` | no |
| 15 | Pure scoring formula | `app/pipeline/score_formula.py` + `tests/test_scoring.py` | yes |
| 16 | Monitor stage | `app/pipeline/monitor.py` | no |
| 17 | Cluster stage | `app/pipeline/cluster.py` | no |
| 18 | Score stage | `app/pipeline/score.py` | no |
| 20 | Act stage | `app/pipeline/act.py` | no |
| 35 | **LLMO probe pipeline** | `app/pipeline/llmo.py` | no |
| 36 | **LLMO scoring (pure)** | `app/pipeline/llmo_scoring.py` + `tests/test_llmo_scoring.py` | yes |
| 37 | **Brand-level rollup** | `app/pipeline/brand_scoring.py` | no |

## Setup

```bash
cd ../pulse-worktrees/track-1-engine/backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Allowed imports

You may import from `app.config`, `app.models`, and your own new files. **Do not import from `app.api.*`, `app.adapters.*`, `app.destinations.*`, or `app.workers.*`** — those belong to Track 2 and will not exist on your branch.

## Verification

```bash
pytest tests/ -v   # all tests must pass
python -c "from app.pipeline import monitor, cluster, score, act, llmo, llmo_scoring, brand_scoring; print('ok')"
```

## Hand-back

When all 13 tasks are committed on `track-1-engine`, push the branch and notify the integrator. The integrator will merge into `main` after Track 2 and Track 3 are also ready.

## Notes

- The "ClickHouse `ALTER TABLE posts UPDATE ...` reassignment" in `cluster.py` is asynchronous in CH — that's OK; the SummingMergeTree MV catches up at merge time.
- For Task 35 (LLMO probe), **do not call real Anthropic/OpenAI/Perplexity APIs.** Use Gemini with the 4 system prompts from the plan — same shape, free-tier-friendly, deterministic.
- `gemini-1.5-flash` for sentiment + the judge pass. `gemini-1.5-pro` for response drafting only.
