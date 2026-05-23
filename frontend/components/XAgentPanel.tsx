"use client";
import { useState } from "react";
import clsx from "clsx";

type Gates = {
  author_ok: boolean;
  keyword_ok: boolean;
  relevance: { relevant: boolean; confidence: number; reason: string } | null;
};

type ReplyResponse = {
  tweet: { id: string; author_handle: string; text: string; created_at: string | null };
  gates: Gates;
  draft: string | null;
  compose_url: string | null;
  already_processed: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function XAgentPanel() {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ReplyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [force, setForce] = useState(false);

  async function run() {
    if (!url.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/api/x_agent/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tweet_url: url.trim(), force }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`HTTP ${res.status}: ${body.slice(0, 200)}`);
      }
      const data = (await res.json()) as ReplyResponse;
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ink-glass rounded-sm p-6 rise" style={{ animationDelay: "180ms" }}>
      <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
        <h3 className="eyebrow">X AGENT · OPERATOR-TRIGGERED</h3>
        <span className="num text-[10px] text-paper-mute">groq · oembed · x intent</span>
      </div>

      <div className="space-y-3">
        <div className="flex gap-2 flex-wrap">
          <input
            type="url"
            placeholder="https://x.com/bruhwhat4110/status/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !busy) run(); }}
            className="flex-1 min-w-[260px] bg-ink-900/60 border rule rounded-sm px-3 py-2 text-sm text-paper num placeholder:text-paper-mute focus:outline-none focus:border-signal"
          />
          <label className="flex items-center gap-2 text-[11px] text-paper-mute">
            <input
              type="checkbox"
              checked={force}
              onChange={(e) => setForce(e.target.checked)}
              className="accent-signal"
            />
            force (skip gates)
          </label>
          <button
            onClick={run}
            disabled={busy || !url.trim()}
            className={clsx(
              "px-5 py-2 rounded-sm font-mono text-[11px] tracking-terminal uppercase border transition-all",
              busy
                ? "border-ink-600 text-paper-mute cursor-wait"
                : "border-signal text-signal bg-signal/10 hover:bg-signal/20 active:scale-[0.98]",
            )}
          >
            {busy ? "running…" : "run agent"}
          </button>
        </div>

        {busy && (
          <div className="text-sm text-paper-dim flex items-center gap-2 num">
            <span className="inline-block w-2 h-2 rounded-full bg-signal animate-pulse" />
            fetching tweet · running gates · drafting with groq…
          </div>
        )}

        {error && (
          <div className="border border-alarm/40 bg-alarm/5 rounded-sm p-3 text-sm text-alarm num">
            {error}
          </div>
        )}

        {result && <Trace result={result} />}
      </div>
    </section>
  );
}

function Trace({ result }: { result: ReplyResponse }) {
  const { tweet, gates, draft, compose_url, already_processed } = result;

  return (
    <div className="space-y-3 mt-2 rise">
      {/* fetched tweet */}
      <Row label="FETCH" status="ok">
        <span className="text-paper-dim text-[11px] num">@{tweet.author_handle}</span>
        <span className="text-paper-mute"> · </span>
        <span className="text-paper">{truncate(tweet.text, 160)}</span>
      </Row>

      {/* author gate */}
      <Row label="AUTHOR" status={gates.author_ok ? "ok" : "fail"}>
        {gates.author_ok ? "matches target handle" : "does not match target handle"}
      </Row>

      {/* keyword gate */}
      <Row label="KEYWORD" status={gates.keyword_ok ? "ok" : "fail"}>
        {gates.keyword_ok ? "'crosby' found" : "'crosby' not present"}
      </Row>

      {/* relevance gate */}
      {gates.relevance && (
        <Row label="RELEVANCE" status={gates.relevance.relevant ? "ok" : "fail"}>
          <span className="num text-[11px] text-paper-mute mr-2">
            conf {gates.relevance.confidence.toFixed(2)}
          </span>
          {gates.relevance.reason}
        </Row>
      )}

      {/* draft */}
      {draft && (
        <div className="border rule rounded-sm p-4 bg-ink-900/40">
          <div className="eyebrow mb-2 text-signal">DRAFT · GROQ LLAMA-3.3-70B</div>
          <p className="text-paper text-[15px] leading-relaxed">{draft}</p>
          <div className="num text-[10px] text-paper-mute mt-2">{draft.length} chars</div>
        </div>
      )}

      {/* approve button */}
      {compose_url && (
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <span className="text-[11px] text-paper-mute num">
            {already_processed
              ? "previously processed — re-running with force"
              : "awaiting human approval"}
          </span>
          <a
            href={compose_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2 rounded-sm font-mono text-[11px] tracking-terminal uppercase border border-signal text-ink-900 bg-signal hover:bg-signal/90 active:scale-[0.98] transition-all"
          >
            approve & open in X →
          </a>
        </div>
      )}

      {/* skipped state */}
      {!draft && (
        <div className="text-[12px] text-paper-mute num">
          pipeline stopped before draft — gate failed (see above)
        </div>
      )}
    </div>
  );
}

function Row({
  label, status, children,
}: {
  label: string;
  status: "ok" | "fail";
  children: React.ReactNode;
}) {
  const cls = status === "ok" ? "text-signal" : "text-alarm";
  return (
    <div className="flex items-baseline gap-3 text-sm flex-wrap">
      <span className={clsx("num text-[10px] tracking-terminal w-20 shrink-0", cls)}>
        {status === "ok" ? "✓" : "✗"} {label}
      </span>
      <span className="text-paper-dim flex-1 min-w-0">{children}</span>
    </div>
  );
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n - 1) + "…";
}
