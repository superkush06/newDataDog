# Pulse

Social listening + action pipeline. Monitor → Cluster → Score → Act.

- **Design spec:** `docs/superpowers/specs/2026-05-23-pulse-design.md`
- **Implementation plan:** `docs/superpowers/plans/2026-05-23-pulse-implementation.md`
- **Track handoffs:** `docs/superpowers/handoffs/track-{1,2,3}.md`

## Quickstart (after all tracks merge)

**Single global `.env` at the repo root** powers both backend and frontend.

```bash
# 0. Credentials — one file for everything
cp .env.example .env       # fill in GEMINI_API_KEY, CLICKHOUSE_*, DATABASE_URL,
                           # NIMBLE_API_KEY, REDIS_URL, DD_API_KEY, NEXT_PUBLIC_*

# 1. Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python scripts/verify_env.py        # pings every service, shows what works
python scripts/apply_migrations.py  # ClickHouse + Postgres+pgvector
uvicorn app.main:app --reload &
arq app.workers.pipeline_worker.WorkerSettings &

# 2. Frontend (after track-3 merges)
cd ../frontend && npm install
# Next.js auto-loads NEXT_PUBLIC_* from ../.env via next.config.js
npm run dev
```

### Env layout

```
newDataDog/
├── .env          ← single source of truth (gitignored)
├── .env.example  ← template (committed)
├── backend/      ← reads ../.env via pydantic-settings
└── frontend/     ← reads ../.env via next.config.js (when track-3 lands)
```

Backend `app/config.py` resolves the file via
`Path(__file__).resolve().parents[2] / ".env"` so it works from any cwd.

## Parallel execution

Three worktrees run in parallel:
- `track-1-engine` → backend core + pipeline
- `track-2-surface` → backend adapters + api + workers + destinations + main.py + seed
- `track-3-frontend` → Next.js dashboard

Integrator merges all three back into `main`, then runs Task 33 (smoke test).
