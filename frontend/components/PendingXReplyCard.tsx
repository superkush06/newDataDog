"use client";
import { useState } from "react";
import clsx from "clsx";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Hard-coded demo card — represents the X-reply action staged by Pulse's
// monitor. Click "Approve & post" → calls /api/x_agent/reply, drops the draft
// in clipboard, opens X intent compose pre-filled. One click after that and
// the reply is live as @ryanfding.
const TWEET_URL = "https://x.com/bruhwhat4110/status/2058289631678836895";
const TWEET_PREVIEW =
  "Crosby - The entire strategy seems built around sounding smarter and more disruptive than everyone else while delivering the same half-finished execution we've already seen a dozen times before. Even the community around it feels more focused on defending the image.";

type ReplyResponse = {
  tweet: { id: string; author_handle: string; text: string };
  gates: {
    author_ok: boolean;
    keyword_ok: boolean;
    relevance: { relevant: boolean; confidence: number; reason: string } | null;
  };
  draft: string | null;
  compose_url: string | null;
};

export function PendingXReplyCard() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ReplyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function approve() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/api/x_agent/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tweet_url: TWEET_URL, force: true }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as ReplyResponse;
      setResult(data);
      // copy draft, then open compose tab so the X reply window pops as part of the click
      if (data.draft && navigator.clipboard) {
        try { await navigator.clipboard.writeText(data.draft); } catch { /* noop */ }
      }
      if (data.compose_url) {
        window.open(data.compose_url, "_blank", "noopener,noreferrer");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="ink-glass rounded-sm overflow-hidden border-l-2 border-l-signal">
      <div className="px-5 py-4 space-y-3">
        {/* header row */}
        <div className="flex items-center gap-2 text-[10px] num tracking-terminal flex-wrap">
          <span className="px-1.5 py-0.5 border border-signal/40 text-signal bg-signal/5 rounded-sm">
            X · REPLY
          </span>
          <span className="px-1.5 py-0.5 border border-warn/40 text-warn bg-warn/5 rounded-sm">
            HIGH
          </span>
          <span className="text-paper-mute">·</span>
          <span className="text-paper-dim">posted by @bruhwhat4110 · 2m ago</span>
          <span className="ml-auto eyebrow text-paper-mute">PENDING</span>
        </div>

        {/* tweet preview */}
        <div className="border rule rounded-sm p-3 bg-ink-900/40">
          <div className="eyebrow text-[9px] text-paper-mute mb-1">SOURCE TWEET</div>
          <p className="text-paper text-[14px] leading-relaxed">{TWEET_PREVIEW}</p>
        </div>

        {/* trace OR action button */}
        {!result && !busy && !error && (
          <div className="flex items-center justify-between gap-3 flex-wrap pt-1">
            <div className="text-[12px] text-paper-dim">
              Pulse will draft a reply with Groq and open X for your approval.
            </div>
            <button
              onClick={approve}
              className="px-5 py-2 rounded-sm font-mono text-[11px] tracking-terminal uppercase border border-signal bg-signal text-ink-900 hover:bg-signal/90 active:scale-[0.98] transition-all"
            >
              approve &amp; post →
            </button>
          </div>
        )}

        {busy && (
          <div className="text-sm text-paper-dim flex items-center gap-2 num pt-1">
            <span className="inline-block w-2 h-2 rounded-full bg-signal animate-pulse" />
            agent running · fetch → gate → draft → opening X…
          </div>
        )}

        {error && (
          <div className="border border-alarm/40 bg-alarm/5 rounded-sm p-3 text-sm text-alarm num">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-2 rise">
            <Row label="FETCH"     ok={true}>{`@${result.tweet.author_handle}`}</Row>
            <Row label="AUTHOR"    ok={result.gates.author_ok}>matches target handle</Row>
            <Row label="KEYWORD"   ok={result.gates.keyword_ok}>'crosby' present</Row>
            {result.gates.relevance && (
              <Row label="RELEVANCE" ok={result.gates.relevance.relevant}>
                <span className="num text-[11px] mr-2 text-paper-mute">
                  conf {result.gates.relevance.confidence.toFixed(2)}
                </span>
                {result.gates.relevance.reason}
              </Row>
            )}
            {result.draft && (
              <div className="border rule rounded-sm p-3 bg-ink-900/40 mt-2">
                <div className="eyebrow text-[9px] text-signal mb-1">PULSE DRAFT · GROQ</div>
                <p className="text-paper text-[14px] leading-relaxed">{result.draft}</p>
              </div>
            )}
            {result.compose_url && (
              <div className="flex items-center justify-between gap-3 pt-1 flex-wrap">
                <span className="text-[11px] text-paper-mute num">
                  ✓ X opened — one click to post (draft copied to clipboard)
                </span>
                <a
                  href={result.compose_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-1.5 rounded-sm font-mono text-[10px] tracking-terminal uppercase border border-signal text-signal hover:bg-signal/10 transition-all"
                >
                  re-open in X
                </a>
              </div>
            )}
          </div>
        )}
      </div>
    </article>
  );
}

function Row({
  label, ok, children,
}: {
  label: string;
  ok: boolean;
  children: React.ReactNode;
}) {
  const cls = ok ? "text-signal" : "text-alarm";
  return (
    <div className="flex items-baseline gap-3 text-sm flex-wrap">
      <span className={clsx("num text-[10px] tracking-terminal w-20 shrink-0", cls)}>
        {ok ? "✓" : "✗"} {label}
      </span>
      <span className="text-paper-dim flex-1 min-w-0">{children}</span>
    </div>
  );
}
