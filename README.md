# Pulse

Social listening + action pipeline. Monitor → Cluster → Score → Act.

- **Design spec:** `docs/superpowers/specs/2026-05-23-pulse-design.md`
- **Implementation plan:** `docs/superpowers/plans/2026-05-23-pulse-implementation.md`
- **Track handoffs:** `docs/superpowers/handoffs/track-{1,2,3}.md`

## Quickstart (after all tracks merge)

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in keys
python scripts/apply_migrations.py
uvicorn app.main:app --reload &
arq app.workers.pipeline_worker.WorkerSettings &

# Frontend
cd ../frontend && npm install
cp .env.local.example .env.local  # set NEXT_PUBLIC_DEMO_BRAND_ID
npm run dev
```

## Parallel execution

Three worktrees run in parallel:
- `track-1-engine` → backend core + pipeline
- `track-2-surface` → backend adapters + api + workers + destinations + main.py + seed
- `track-3-frontend` → Next.js dashboard

Integrator merges all three back into `main`, then runs Task 33 (smoke test).
