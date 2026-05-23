import { SeverityBadge } from "./SeverityBadge";
import { SentimentBar } from "./SentimentBar";
import type { Cluster } from "@/lib/types";

export function ClusterCard({ cluster }: { cluster: Cluster }) {
  return (
    <article className="ink-glass rounded-sm p-5 flex flex-col gap-3 group hover:bg-ink-800/60 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display font-bold text-paper text-lg leading-tight flex-1">
          {cluster.name}
        </h3>
        <SeverityBadge severity={cluster.severity} />
      </div>

      <p className="text-sm text-paper-dim leading-relaxed line-clamp-3">
        {cluster.summary}
      </p>

      <SentimentBar breakdown={cluster.sentiment_breakdown} />

      {cluster.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {cluster.tags.map((t) => (
            <span key={t} className="font-mono text-[10px] tracking-terminal px-1.5 py-0.5 border rule text-paper-dim rounded-sm">
              {t}
            </span>
          ))}
        </div>
      )}

      <div className="flex justify-between items-baseline pt-2 border-t rule mt-1">
        <span className="num text-[11px] text-paper-mute">
          {cluster.post_count} posts
        </span>
        <span className="num text-[11px] text-paper-mute capitalize">
          {cluster.platforms.join(" · ")}
        </span>
        <span className="num font-bold text-paper text-sm">
          {cluster.severity_score.toFixed(0)}
          <span className="text-paper-mute text-[10px]">/1000</span>
        </span>
      </div>
    </article>
  );
}
