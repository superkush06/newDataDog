import type { SentimentBreakdown } from "@/lib/types";

export function SentimentBar({ breakdown }: { breakdown: SentimentBreakdown }) {
  const total = breakdown.positive + breakdown.negative + breakdown.neutral + breakdown.question;
  if (total === 0) return null;

  const pct = (n: number) => `${((n / total) * 100).toFixed(0)}%`;

  return (
    <div className="space-y-1">
      <div className="flex h-2 overflow-hidden rounded-full bg-gray-100">
        <div className="bg-green-500" style={{ width: pct(breakdown.positive) }} />
        <div className="bg-red-500" style={{ width: pct(breakdown.negative) }} />
        <div className="bg-blue-400" style={{ width: pct(breakdown.question) }} />
        <div className="bg-gray-300" style={{ width: pct(breakdown.neutral) }} />
      </div>
      <div className="flex gap-3 text-xs text-gray-500">
        <span className="text-green-600">+{breakdown.positive}</span>
        <span className="text-red-600">−{breakdown.negative}</span>
        <span className="text-blue-500">?{breakdown.question}</span>
        <span>{breakdown.neutral}</span>
      </div>
    </div>
  );
}
