# Track 3 — Frontend (Next.js dashboard + LLMO views)

**Branch:** `track-3-frontend`
**Worktree path:** `../pulse-worktrees/track-3-frontend`
**Owner files:** Everything under `frontend/`

## Your scope

You build the **dashboard** — all UI. Six pages: `/dashboard` (main hero), `/feed`, `/clusters`, `/queue`, `/llmo`, `/actions`. You can develop against a mock JSON server until Track 2 is merged.

## Read first

- Spec: `docs/superpowers/specs/2026-05-23-pulse-design.md` (especially §6 UI surfaces, §A.7 LLMO frontend, §A.9 demo narrative)
- Plan: `docs/superpowers/plans/2026-05-23-pulse-implementation.md`

## Your tasks (in order)

| # | Task | File(s) |
|---|---|---|
| 26 | Next.js + Tailwind + TanStack scaffold | `frontend/` (create-next-app) |
| 27 | Shared types + API client | `frontend/lib/{types,api}.ts` |
| 28 | Providers + root layout + nav | `frontend/app/{providers,layout,page}.tsx` |
| 29 | Live Feed view | `frontend/app/feed/page.tsx` + PostCard + FeedSidebar + useFeed |
| 30 | Clusters view | ClusterCard + SeverityBadge + SentimentBar + useClusters |
| 31 | Priority Queue view | QueueTable + useQueue |
| 32 | Actions view | ActionCard + useActions |
| 41 | **`/dashboard` main page + ScoreHero** | `frontend/app/dashboard/` + ScoreHero + useScores |
| 42 | **`/llmo` view + LLMVisibilityGrid + PromptResults** | `frontend/app/llmo/` + components + useLLMOAudits |
| 43 | **GroundTruthDriftCard in Actions** | new component + update actions/page.tsx |

## Setup

```bash
cd ../pulse-worktrees/track-3-frontend
npx --yes create-next-app@14 frontend --typescript --tailwind --app --no-eslint --import-alias "@/*" --use-npm <<< "y"
cd frontend
npm install @tanstack/react-query@5.17.0 recharts@2.10.0 zustand@4.5.0 clsx@2.1.0 @supabase/supabase-js@2.39.0
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_URL=http://localhost:8000
# leave NEXT_PUBLIC_DEMO_BRAND_ID empty until Track 2 seeds one
```

## Dev-loop without backend

Run a one-file mock server while Track 2 is building. Save this as `frontend/mock-server.mjs` (and `.gitignore` it):

```js
import { createServer } from "node:http";
const j = (res, data) => { res.setHeader("content-type","application/json"); res.end(JSON.stringify(data)); };
createServer((req, res) => {
  res.setHeader("access-control-allow-origin","*");
  if (req.url.startsWith("/api/scores")) return j(res, {
    overall: 73, social: 81, llmo: 65,
    social_breakdown: { critical_clusters: 1, high_clusters: 2, medium_clusters: 3 },
    llmo_breakdown: {
      citation_frequency: 60, share_of_voice: 45, citation_accuracy: 78, sentiment_quality: 70,
      per_llm: {
        claude: { score: 87, mention_rate: 95, avg_position: 1.4, drift: "low" },
        chatgpt: { score: 61, mention_rate: 80, avg_position: 2.6, drift: "high" },
        gemini: { score: 78, mention_rate: 90, avg_position: 1.8, drift: "medium" },
        perplexity: { score: 82, mention_rate: 88, avg_position: 1.5, drift: "low" },
      },
    },
    sparklines: { overall: [70,71,72,73], social: [80,81,81,81], llmo: [60,62,64,65] },
  });
  if (req.url.startsWith("/api/feed")) return j(res, { posts: [], next_cursor: null, stats: { volume_24h: 0, sentiment_7d: [], platform_distribution: {}, avg_response_minutes: 0 }});
  if (req.url.startsWith("/api/clusters")) return j(res, { clusters: [], total: 0 });
  if (req.url.startsWith("/api/queue")) return j(res, { queue: [], threshold_config: {critical:700,high:400,medium:200}, weights: {volume:10,like:2,share:5,comment:3,sentiment:3.5} });
  if (req.url.startsWith("/api/actions")) return j(res, { actions: [], total: 0 });
  if (req.url.startsWith("/api/llmo/audits")) return j(res, { audits: [] });
  return j(res, { ok: true });
}).listen(8000, () => console.log("mock on 8000"));
```

Run with `node mock-server.mjs &`. Replace with `npm run dev` against the real backend once Track 2 ships.

## Verification

```bash
npm run dev
# open http://localhost:3000 → should land on /dashboard with the mock numbers
```

Visual checklist:
- `/dashboard` shows 3 big numbers (Overall, Social, LLMO) side by side with sparklines and color bands (green/amber/rose).
- `/llmo` shows the 4-LLM grid with drift colors.
- `/actions` renders `ground_truth_correction` cards differently (rose background) from regular response cards.

## Hand-back

Push `track-3-frontend`. Integrator merges last (depends only on Track 2's API contract, not Track 1).
