import clsx from "clsx";
import type { LLMName, LLMScore } from "@/lib/types";

const LLM_META: Record<LLMName, { label: string; tag: string; dot: string }> = {
  claude:     { label: "Claude",     tag: "Anthropic", dot: "#D88A4E" },
  chatgpt:    { label: "ChatGPT",    tag: "OpenAI",    dot: "#5BC59F" },
  gemini:     { label: "Gemini",     tag: "Google",    dot: "#7CC8FF" },
  perplexity: { label: "Perplexity", tag: "Perplexity",dot: "#B89CE0" },
};

const DRIFT_TONE: Record<string, { label: string; cls: string }> = {
  low:    { label: "low drift",    cls: "text-signal border-signal/40 bg-signal/5" },
  medium: { label: "medium drift", cls: "text-warn border-warn/40 bg-warn/5" },
  high:   { label: "high drift",   cls: "text-alarm border-alarm/40 bg-alarm/5 animate-shimmer" },
};

function LLMCard({ name, score }: { name: LLMName; score: LLMScore }) {
  const meta = LLM_META[name];
  const drift = DRIFT_TONE[score.drift];
  const tone =
    score.score >= 70 ? "text-signal"
    : score.score >= 40 ? "text-warn"
    : "text-alarm";

  return (
    <div className="ink-glass rounded-sm p-5 flex flex-col gap-4 group hover:bg-ink-800/60 transition-colors">
      <div className="flex items-center gap-2">
        <span
          className="w-2 h-2 rounded-full shrink-0"
          style={{ background: meta.dot, boxShadow: `0 0 8px ${meta.dot}` }}
        />
        <span className="font-display font-bold text-paper text-lg leading-none">
          {meta.label}
        </span>
        <span className="num text-[10px] text-paper-mute uppercase tracking-wider ml-auto">
          {meta.tag}
        </span>
      </div>

      <div className="flex items-baseline gap-2">
        <span className={clsx("font-display font-black leading-none text-5xl", tone)}>
          {score.score.toFixed(0)}
        </span>
        <span className="num text-paper-mute text-xs mb-1.5">/100</span>
      </div>

      <div className={clsx("inline-flex w-fit eyebrow text-[10px] px-2 py-1 border rounded-sm", drift.cls)}>
        {drift.label}
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12px] mt-1">
        <span className="text-paper-mute">Mentioned</span>
        <span className="num text-paper text-right">
          {score.mention_rate?.toFixed(0)}%
        </span>
        <span className="text-paper-mute">Avg position</span>
        <span className="num text-paper text-right">
          {score.avg_position > 0 ? `P${score.avg_position?.toFixed(1)}` : "—"}
        </span>
      </div>
    </div>
  );
}

export function LLMVisibilityGrid({
  perLlm,
}: {
  perLlm: Record<LLMName, LLMScore>;
}) {
  const names = (Object.keys(perLlm) as LLMName[]).filter((n) => LLM_META[n]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {names.map((name, i) => (
        <div key={name} className="rise" style={{ animationDelay: `${100 + i * 80}ms` }}>
          <LLMCard name={name} score={perLlm[name]} />
        </div>
      ))}
    </div>
  );
}
