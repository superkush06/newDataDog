"use client";
import { useState } from "react";
import clsx from "clsx";

/**
 * A two-tier explainer: a compact strip of the four LLMO sub-metrics with
 * their weights, expandable into long-form prose. Lives on the dashboard so
 * any user can answer "wait, how is this calculated?" without leaving the page.
 */

type Metric = {
  code: string;
  name: string;
  weight: number;
  range: string;
  short: string;
  long: string;
};

const LLMO_METRICS: Metric[] = [
  {
    code: "CF",
    name: "Citation Frequency",
    weight: 30,
    range: "0–100",
    short: "How often the brand is cited at all when asked relevant prompts.",
    long: "For each seeded prompt × LLM combination we count whether the brand surfaced. The metric is the percentage of runs in which the brand appeared anywhere in the response. Position-weighted: a P1 headline mention counts 1.0, P2 early ≈ 0.7, P3 body ≈ 0.4, P4 list ≈ 0.2.",
  },
  {
    code: "SoV",
    name: "Share of Voice",
    weight: 25,
    range: "0–100",
    short: "What fraction of the competitive mention-set is yours.",
    long: "For prompts where competitors are also named, we divide your brand's mention count by total brand-mentions in the responses (your brand + each declared competitor). A 25% SoV in a 4-competitor field is parity; > 40% is dominance; < 10% is invisibility.",
  },
  {
    code: "CA",
    name: "Citation Accuracy",
    weight: 25,
    range: "0–100",
    short: "When you ARE mentioned, how factually correct is the claim?",
    long: "Each response is judged against your ground-truth brand description using llama-3.1-8b-instant as the judge model. The drift_score (0 = perfect, 1 = total fabrication) is inverted and aggregated. Hallucinated facts about your brand drag this down fast.",
  },
  {
    code: "SQ",
    name: "Sentiment Quality",
    weight: 20,
    range: "0–100",
    short: "When mentioned, is the framing positive, neutral, or hostile?",
    long: "Per-mention sentiment is scored −1 to +1 by the judge model, then normalized to 0–100. A score of 50 means consistently neutral; 70+ means positively framed; 30 or less suggests the model frames your brand in a damaging light.",
  },
];

export function ScoringMethod() {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <section className="ink-glass rounded-sm p-6 rise" style={{ animationDelay: "120ms" }}>
      <div className="flex items-baseline justify-between mb-5">
        <h3 className="eyebrow">HOW THIS IS SCORED</h3>
        <span className="num text-[10px] text-paper-mute">methodology · v0.1</span>
      </div>

      {/* SOCIAL SCORE explainer (compact, single line) */}
      <div className="mb-6 pb-6 border-b rule">
        <div className="flex items-baseline gap-3 mb-2">
          <span className="font-display font-bold text-2xl text-paper">Social Score</span>
          <span className="num text-paper-mute text-xs">= 100 − severity pressure</span>
        </div>
        <p className="text-sm text-paper-dim leading-relaxed max-w-3xl">
          Every active cluster carries a weight by severity:{" "}
          <span className="num text-alarm">critical × 30</span>,{" "}
          <span className="num text-warn">high × 15</span>,{" "}
          <span className="num text-cool">medium × 5</span>. We sum the pressure
          across the last 24 hours and subtract from 100. No active issues → score
          is 100. A single critical cluster is a 30-point hit.
        </p>
      </div>

      {/* LLMO SCORE explainer (interactive grid) */}
      <div className="flex items-baseline gap-3 mb-4">
        <span className="font-display font-bold text-2xl text-paper">LLMO Score</span>
        <span className="num text-paper-mute text-xs">
          = 0.30·CF + 0.25·SoV + 0.25·CA + 0.20·SQ
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {LLMO_METRICS.map((m) => {
          const isOpen = open === m.code;
          return (
            <button
              key={m.code}
              onClick={() => setOpen(isOpen ? null : m.code)}
              className={clsx(
                "text-left p-4 rounded-sm border transition-all",
                "hover:bg-ink-800/60",
                isOpen
                  ? "bg-ink-800 border-signal/40"
                  : "bg-ink-900/40 border-ink-600",
              )}
            >
              <div className="flex items-baseline justify-between mb-1.5">
                <span className="font-mono text-[10px] tracking-terminal text-signal">
                  {m.code}
                </span>
                <span className="num text-[10px] text-paper-mute">w={m.weight}%</span>
              </div>
              <div className="font-display font-semibold text-paper text-lg leading-tight mb-2">
                {m.name}
              </div>
              <p className="text-[12px] text-paper-dim leading-snug">{m.short}</p>
              <div
                className={clsx(
                  "mt-3 text-[12px] text-paper leading-relaxed overflow-hidden transition-all",
                  isOpen ? "max-h-[400px] opacity-100" : "max-h-0 opacity-0",
                )}
              >
                <div className="pt-3 border-t rule">{m.long}</div>
              </div>
              <div className="mt-3 eyebrow text-[10px] text-paper-mute">
                {isOpen ? "← collapse" : "click for detail →"}
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
