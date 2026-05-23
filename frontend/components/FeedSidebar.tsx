"use client";
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FeedStats, Post } from "@/lib/types";

function subFromPermalink(permalink: string | undefined): string | null {
  if (!permalink) return null;
  const m = permalink.match(/reddit\.com\/r\/([^/]+)/i);
  return m ? `r/${m[1]}` : null;
}

export function FeedSidebar({
  stats,
  posts,
}: {
  stats: FeedStats;
  posts?: Post[];
}) {
  // synthesize top subreddits from posts since the backend's
  // platform_distribution is platform-level, not sub-level
  const subCounts = new Map<string, number>();
  (posts ?? []).forEach((p) => {
    const sub = subFromPermalink(p.permalink);
    if (sub) subCounts.set(sub, (subCounts.get(sub) ?? 0) + 1);
  });
  const topSubs = Array.from(subCounts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 6);

  return (
    <aside className="w-72 shrink-0 space-y-4">
      <div className="ink-glass rounded-sm p-5 rise">
        <div className="eyebrow mb-2">VOLUME / 24h</div>
        <p className="font-display font-black text-paper text-5xl leading-none num">
          {stats.volume_24h.toLocaleString()}
        </p>
        <p className="num text-[11px] text-paper-mute mt-1">reddit mentions</p>
      </div>

      {stats.sentiment_7d.length > 0 && (
        <div className="ink-glass rounded-sm p-5 rise" style={{ animationDelay: "80ms" }}>
          <div className="eyebrow mb-3">SENTIMENT / 7d</div>
          <ResponsiveContainer width="100%" height={84}>
            <LineChart data={stats.sentiment_7d}>
              <XAxis dataKey="date" hide />
              <YAxis hide />
              <Tooltip />
              <Line type="monotone" dataKey="positive" stroke="#C5F73A" dot={false} strokeWidth={1.5} />
              <Line type="monotone" dataKey="negative" stroke="#FF4D4D" dot={false} strokeWidth={1.5} />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-4 num text-[11px] mt-2">
            <span className="text-signal">━ positive</span>
            <span className="text-alarm">━ negative</span>
          </div>
        </div>
      )}

      {topSubs.length > 0 && (
        <div className="ink-glass rounded-sm p-5 rise" style={{ animationDelay: "160ms" }}>
          <div className="eyebrow mb-3">TOP SUBREDDITS</div>
          <ul className="space-y-2">
            {topSubs.map(([sub, n]) => {
              const max = topSubs[0][1];
              return (
                <li key={sub} className="space-y-1">
                  <div className="flex justify-between text-[12px]">
                    <span className="text-reddit num">{sub}</span>
                    <span className="num text-paper">{n}</span>
                  </div>
                  <div className="h-1 bg-ink-700 rounded-full overflow-hidden">
                    <div className="h-full bg-reddit" style={{ width: `${(n / max) * 100}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <div className="ink-glass rounded-sm p-5 rise" style={{ animationDelay: "240ms" }}>
        <div className="eyebrow mb-2">AVG RESPONSE</div>
        <p className="font-display font-bold text-paper text-3xl num">
          {stats.avg_response_minutes > 0 ? `${stats.avg_response_minutes}m` : "—"}
        </p>
        <p className="text-[11px] text-paper-mute mt-1">time-to-action on flagged threads</p>
      </div>
    </aside>
  );
}
