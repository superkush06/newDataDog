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
    <div className="ink-glass rounded-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b rule">
              <th className="px-4 py-3 text-left eyebrow">Cluster</th>
              <th className="px-4 py-3 text-right eyebrow">vol&times;{weights.volume}</th>
              <th className="px-4 py-3 text-right eyebrow">engage</th>
              <th className="px-4 py-3 text-right eyebrow">sentmnt</th>
              <th className="px-4 py-3 text-right eyebrow">velocty</th>
              <th className="px-4 py-3 text-right eyebrow">infl</th>
              <th className="px-4 py-3 text-right eyebrow">score</th>
              <th className="px-4 py-3 eyebrow">severity</th>
            </tr>
          </thead>
          <tbody className="divide-y rule">
            {items.map((item) => {
              const sb = item.score_breakdown;
              return (
                <tr key={item.id} className="hover:bg-ink-800/60 transition-colors">
                  <td className="px-4 py-3 font-display text-paper max-w-[260px] truncate">
                    {item.name}
                  </td>
                  <td className="px-4 py-3 text-right num text-paper-dim">{fmt(sb?.volume ?? 0)}</td>
                  <td className="px-4 py-3 text-right num text-paper-dim">{fmt(sb?.engagement ?? 0)}</td>
                  <td className="px-4 py-3 text-right num text-paper-dim">{fmt(sb?.sentiment ?? 0)}</td>
                  <td className="px-4 py-3 text-right num text-paper-dim">{fmt(sb?.velocity ?? 0)}</td>
                  <td className="px-4 py-3 text-right num text-paper-dim">{sb?.influence_multiplier ?? 1}×</td>
                  <td className="px-4 py-3 text-right num font-bold text-paper">{fmt(item.severity_score)}</td>
                  <td className="px-4 py-3"><SeverityBadge severity={item.severity} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="border-t rule px-4 py-3 flex gap-6 num text-[11px] text-paper-mute flex-wrap">
        <span className="text-alarm">critical ≥ {thresholds.critical}</span>
        <span className="text-warn">high ≥ {thresholds.high}</span>
        <span className="text-cool">medium ≥ {thresholds.medium}</span>
        <span className="ml-auto">weights · volume {weights.volume} / engagement (likes {weights.like} · shares {weights.share} · comments {weights.comment}) / sentiment {weights.sentiment}</span>
      </div>
    </div>
  );
}
