import type { SentimentBreakdown } from "@/lib/types";

export function SentimentBar({ breakdown }: { breakdown: SentimentBreakdown }) {
  const total = breakdown.positive + breakdown.negative + breakdown.neutral + breakdown.question;
  if (total === 0) return null;

  const pct = (n: number) => `${((n / total) * 100).toFixed(0)}%`;

  return (
    <div className="space-y-2">
      <div className="flex h-1.5 overflow-hidden rounded-sm bg-ink-700">
        <div className="bg-signal" style={{ width: pct(breakdown.positive) }} />
        <div className="bg-alarm" style={{ width: pct(breakdown.negative) }} />
        <div className="bg-cool"   style={{ width: pct(breakdown.question) }} />
        <div className="bg-ink-600" style={{ width: pct(breakdown.neutral) }} />
      </div>
      <div className="flex gap-3 num text-[11px] text-paper-mute">
        <span className="text-signal">+{breakdown.positive}</span>
        <span className="text-alarm">−{breakdown.negative}</span>
        <span className="text-cool">?{breakdown.question}</span>
        <span>·{breakdown.neutral}</span>
      </div>
    </div>
  );
}
