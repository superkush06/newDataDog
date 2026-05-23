import { SeverityBadge } from "./SeverityBadge";
import type { QueueItem, ThresholdConfig, QueueWeights } from "@/lib/types";

function fmt(n: number) { return n.toFixed(0); }

export function QueueTable({
  items,
  thresholds,
  weights,
}: {
  items: QueueItem[];
  thresholds: ThresholdConfig;
  weights: QueueWeights;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
            <th className="pb-3 pr-4">Cluster</th>
            <th className="pb-3 pr-4 text-right">Volume ×{weights.volume}</th>
            <th className="pb-3 pr-4 text-right">Engagement</th>
            <th className="pb-3 pr-4 text-right">Sentiment</th>
            <th className="pb-3 pr-4 text-right">Velocity</th>
            <th className="pb-3 pr-4 text-right">Influence</th>
            <th className="pb-3 pr-4 text-right">Score</th>
            <th className="pb-3">Severity</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map((item) => {
            const sb = item.score_breakdown;
            return (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="py-3 pr-4 font-medium text-gray-800 max-w-[200px] truncate">{item.name}</td>
                <td className="py-3 pr-4 text-right text-gray-600">{fmt(sb?.volume ?? 0)}</td>
                <td className="py-3 pr-4 text-right text-gray-600">{fmt(sb?.engagement ?? 0)}</td>
                <td className="py-3 pr-4 text-right text-gray-600">{fmt(sb?.sentiment ?? 0)}</td>
                <td className="py-3 pr-4 text-right text-gray-600">{fmt(sb?.velocity ?? 0)}</td>
                <td className="py-3 pr-4 text-right text-gray-600">{sb?.influence_multiplier ?? 1}×</td>
                <td className="py-3 pr-4 text-right font-semibold text-gray-900">{fmt(item.severity_score)}</td>
                <td className="py-3"><SeverityBadge severity={item.severity} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="mt-4 flex gap-6 text-xs text-gray-400">
        <span>Critical ≥{thresholds.critical}</span>
        <span>High ≥{thresholds.high}</span>
        <span>Medium ≥{thresholds.medium}</span>
      </div>
    </div>
  );
}
