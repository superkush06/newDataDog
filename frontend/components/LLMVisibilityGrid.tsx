import clsx from "clsx";
import type { LLMName, LLMScore } from "@/lib/types";

const LLM_META: Record<LLMName, { label: string; icon: string }> = {
  claude:     { label: "Claude",     icon: "🧡" },
  chatgpt:    { label: "ChatGPT",    icon: "🟢" },
  gemini:     { label: "Gemini",     icon: "🔵" },
  perplexity: { label: "Perplexity", icon: "🔮" },
};

const DRIFT_COLOR: Record<string, string> = {
  low:    "text-green-600 bg-green-50",
  medium: "text-amber-600 bg-amber-50",
  high:   "text-rose-600 bg-rose-50 animate-pulse",
};

function LLMCard({ name, score }: { name: LLMName; score: LLMScore }) {
  const meta = LLM_META[name];
  const color =
    score.score >= 70 ? "text-green-600" : score.score >= 40 ? "text-amber-600" : "text-rose-600";

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xl">{meta.icon}</span>
        <span className="font-semibold text-gray-800">{meta.label}</span>
        <span className={clsx("ml-auto text-xs font-medium px-2 py-0.5 rounded-full", DRIFT_COLOR[score.drift])}>
          {score.drift} drift
        </span>
      </div>
      <p className={clsx("text-4xl font-extrabold", color)}>{score.score}</p>
      <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
        <span>Mention rate</span>
        <span className="font-medium text-gray-700 text-right">{score.mention_rate}%</span>
        <span>Avg position</span>
        <span className="font-medium text-gray-700 text-right">#{score.avg_position?.toFixed(1)}</span>
      </div>
    </div>
  );
}

export function LLMVisibilityGrid({
  perLlm,
}: {
  perLlm: Record<LLMName, LLMScore>;
}) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {(Object.keys(perLlm) as LLMName[]).map((name) => (
        <LLMCard key={name} name={name} score={perLlm[name]} />
      ))}
    </div>
  );
}
