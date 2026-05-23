import type {
  FeedResponse,
  Cluster,
  QueueItem,
  Action,
  LLMAudit,
  ScoreSnapshot,
  ThresholdConfig,
  QueueWeights,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID ?? "";

function url(path: string, params?: Record<string, string>) {
  const u = new URL(`${BASE}${path}`);
  if (BRAND_ID) u.searchParams.set("brand_id", BRAND_ID);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v) u.searchParams.set(k, v);
    }
  }
  return u.toString();
}

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const res = await fetch(url(path, params), { next: { revalidate: 0 } });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

export async function fetchFeed(cursor?: string): Promise<FeedResponse> {
  return get("/api/feed", cursor ? { cursor } : undefined);
}

export async function fetchClusters(params?: {
  status?: string;
  min_severity?: string;
}): Promise<{ clusters: Cluster[]; total: number }> {
  return get("/api/clusters", params as Record<string, string>);
}

export async function fetchQueue(): Promise<{
  queue: QueueItem[];
  threshold_config: ThresholdConfig;
  weights: QueueWeights;
}> {
  return get("/api/queue");
}

export async function fetchActions(params?: {
  type?: string;
  state?: string;
}): Promise<{ actions: Action[]; total: number }> {
  return get("/api/actions", params as Record<string, string>);
}

export async function fetchScores(): Promise<ScoreSnapshot> {
  return get("/api/scores");
}

export async function fetchLLMOAudits(params?: {
  llm?: string;
}): Promise<{ audits: LLMAudit[] }> {
  return get("/api/llmo/audits", params as Record<string, string>);
}

export async function decideAction(
  id: string,
  decision: "approve" | "edit_approve" | "reject",
  editedText?: string,
  rejectReason?: string
): Promise<void> {
  await fetch(`${BASE}/api/actions/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, edited_text: editedText, reject_reason: rejectReason }),
  });
}

export async function triggerLLMProbe(): Promise<void> {
  await fetch(`${BASE}/api/llmo/probe${BRAND_ID ? `?brand_id=${BRAND_ID}` : ""}`, {
    method: "POST",
  });
}
