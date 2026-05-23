import { SeverityBadge } from "./SeverityBadge";
import { SentimentBar } from "./SentimentBar";
import type { Cluster } from "@/lib/types";

export function ClusterCard({ cluster }: { cluster: Cluster }) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-5 space-y-3 border border-gray-100">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 text-sm leading-snug">{cluster.name}</h3>
        <SeverityBadge severity={cluster.severity} />
      </div>
      <p className="text-xs text-gray-500 line-clamp-3">{cluster.summary}</p>
      <SentimentBar breakdown={cluster.sentiment_breakdown} />
      <div className="flex flex-wrap gap-1">
        {cluster.tags.map((t) => (
          <span key={t} className="bg-indigo-50 text-indigo-600 text-xs rounded px-2 py-0.5">
            {t}
          </span>
        ))}
      </div>
      <div className="flex justify-between text-xs text-gray-400 pt-1">
        <span>{cluster.post_count} posts</span>
        <span>{cluster.platforms.join(", ")}</span>
        <span>Score: {cluster.severity_score.toFixed(0)}</span>
      </div>
    </div>
  );
}
