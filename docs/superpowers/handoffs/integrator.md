# Integrator Runbook (You)

You don't write feature code. You merge the 3 worktrees back into `main`, resolve type/contract drift, and run the end-to-end smoke test.

## Phase 1 — While tracks build

Stay on `main`. Watch the 3 branches via:

```bash
git fetch --all
git log --oneline --all --graph -30
```

If a track gets blocked on a shared file (e.g. Track 2 needs to extend `pipeline/act.py` which Track 1 owns), cherry-pick the hook commit from Track 1 into `main`, push, and have Track 2 rebase.

## Phase 2 — Merge order

1. **Merge `track-1-engine` → `main`** first. It's the dependency.
   ```bash
   git merge --no-ff track-1-engine
   pytest backend/tests/ -v   # all green
   ```
2. **Merge `track-2-surface` → `main`** second. It imports from track-1's `app.pipeline.*` and `app.core.*`.
   ```bash
   git merge --no-ff track-2-surface
   pytest backend/tests/ -v
   ```
3. **Merge `track-3-frontend` → `main`** last.
   ```bash
   git merge --no-ff track-3-frontend
   cd frontend && npm install && npm run build
   ```

## Phase 3 — Smoke test (Task 33)

```bash
# 1. Apply all migrations
cd backend && source .venv/bin/activate
python scripts/apply_migrations.py

# 2. Seed
python scripts/seed_demo.py   # Acme + Critical cluster
python scripts/seed_llmo.py crosby   # or `acme` for Acme LLMO ground truth

# 3. Start services (each in its own terminal or background)
uvicorn app.main:app --reload &
arq app.workers.pipeline_worker.WorkerSettings &

# 4. Trigger first LLMO probe
curl -X POST "http://localhost:8000/api/llmo/probe?brand_id=<BRAND_ID>"

# 5. Health
curl -s http://localhost:8000/api/health | python -m json.tool
# Expected: clickhouse + postgres connected

# 6. Scores
curl -s "http://localhost:8000/api/scores?brand_id=<BRAND_ID>" | python -m json.tool
# Expected: overall + social + llmo with sparklines

# 7. Frontend
cd ../frontend
echo "NEXT_PUBLIC_DEMO_BRAND_ID=<BRAND_ID>" >> .env.local
npm run dev
# Open http://localhost:3000 → /dashboard renders 3 numbers
```

## Phase 4 — Clean up worktrees

After successful merge + smoke test:

```bash
git worktree remove ../pulse-worktrees/track-1-engine
git worktree remove ../pulse-worktrees/track-2-surface
git worktree remove ../pulse-worktrees/track-3-frontend
git branch -d track-1-engine track-2-surface track-3-frontend
```

## Common conflicts to expect

| Conflict | Resolution |
|---|---|
| `pipeline_worker.py::WorkerSettings.functions` list | Both Track 2 (Task 24) and Track 2 (Task 38) extend it. Track 2 owns the whole file — should be clean. |
| `pipeline/act.py` extended by Task 40 (Track 2) after Track 1's Task 20 created it | Track 2 appends `run_correction` only; Track 1 owns the original file. Resolve by accepting both. |
| `app/main.py` mounts new routers in Task 38 | Track 2 owns `main.py`. Clean. |
| `frontend/lib/{types,api}.ts` extended in Tasks 41/42 | Track 3 owns the whole file. Clean. |
| `frontend/app/layout.tsx` nav extended in Task 41 | Track 3 owns. Clean. |

If any test fails post-merge, **stop and investigate** — the most common cause is type drift between backend Pydantic models and frontend TypeScript interfaces. Both are in `backend/app/models.py` and `frontend/lib/types.ts`; reconcile field names and shapes.
