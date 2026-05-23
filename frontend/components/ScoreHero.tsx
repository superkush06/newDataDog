"use client";
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import clsx from "clsx";
import type { ScoreSnapshot } from "@/lib/types";
import { ScoreRing } from "./ScoreRing";

function deltaOf(spark?: number[]): number | null {
  if (!spark || spark.length < 2) return null;
  return +(spark[spark.length - 1] - spark[0]).toFixed(2);
}

function SubScore({
  label,
  value,
  sparkline,
  legend,
}: {
  label: string;
  value: number;
  sparkline?: number[];
  legend: string;
}) {
  const tone =
    value >= 70 ? "text-signal"
    : value >= 40 ? "text-warn"
    : "text-alarm";
  const stroke =
    value >= 70 ? "#C5F73A"
    : value >= 40 ? "#E8A33D"
    : "#FF4D4D";
  const d = deltaOf(sparkline);
  const data = (sparkline ?? []).map((v, i) => ({ i, v }));

  return (
    <div className="ink-glass rounded-sm p-5 flex flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <span className="eyebrow">{label}</span>
        {d !== null && (
          <span className={clsx("num text-[11px]", d >= 0 ? "text-signal" : "text-alarm")}>
            {d >= 0 ? "▲" : "▼"} {Math.abs(d).toFixed(2)}
          </span>
        )}
      </div>
      <div className="flex items-end gap-2">
        <span className={clsx("font-display font-black leading-none text-6xl", tone)}>
          {value.toFixed(0)}
        </span>
        <span className="num text-paper-mute text-xs mb-2">/100</span>
      </div>
      {data.length > 1 && (
        <div className="-mx-1 h-9">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <YAxis hide domain={[0, 100]} />
              <Tooltip
                cursor={{ stroke: "#2A2724" }}
                formatter={(v: number) => [v.toFixed(2), label]}
                labelFormatter={() => ""}
              />
              <Line
                type="monotone"
                dataKey="v"
                stroke={stroke}
                strokeWidth={1.5}
                dot={false}
                isAnimationActive
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="text-[11px] text-paper-mute leading-snug">{legend}</p>
    </div>
  );
}

export function ScoreHero({ snapshot }: { snapshot: ScoreSnapshot }) {
  const overallTone =
    snapshot.overall >= 70 ? "signal" : snapshot.overall >= 40 ? "warn" : "alarm";

  return (
    <section className="grid grid-cols-1 lg:grid-cols-[1.05fr_1.95fr] gap-6 rise">
      {/* hero ring */}
      <div className="ink-glass rounded-sm p-8 flex flex-col items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 grid-lines opacity-40 pointer-events-none" />
        <span className="eyebrow self-start mb-4">PULSE SCORE</span>
        <ScoreRing value={snapshot.overall} size={260} label="OVERALL" />
        <p className="mt-6 text-xs text-paper-dim text-center max-w-[260px] leading-relaxed">
          Composite of all signals. 50% social listening, 50% LLM visibility.
          Updated every 30 seconds.
        </p>
        <div className={clsx(
          "absolute top-6 right-6 px-2 py-1 eyebrow text-[10px]",
          overallTone === "signal" ? "text-signal" : overallTone === "warn" ? "text-warn" : "text-alarm",
        )}>
          ● {overallTone === "signal" ? "HEALTHY" : overallTone === "warn" ? "ATTENTION" : "AT RISK"}
        </div>
      </div>

      {/* sub-scores */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <SubScore
          label="SOCIAL SCORE"
          value={snapshot.social}
          sparkline={snapshot.sparklines?.social}
          legend="100 minus severity pressure from active clusters in the last 24 hours."
        />
        <SubScore
          label="LLMO SCORE"
          value={snapshot.llmo}
          sparkline={snapshot.sparklines?.llmo}
          legend="Weighted measure of how Claude, ChatGPT, Gemini, and Perplexity cite and describe your brand."
        />
        <div className="ink-glass rounded-sm p-5 sm:col-span-2">
          <div className="flex items-baseline justify-between mb-3">
            <span className="eyebrow">FORMULA</span>
            <span className="num text-[10px] text-paper-mute">live recompute · arq worker</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-2 num text-[12px] leading-relaxed">
            <div>
              <span className="text-paper-mute">Overall&nbsp;=&nbsp;</span>
              <span className="text-paper">0.5 · Social + 0.5 · LLMO</span>
            </div>
            <div>
              <span className="text-paper-mute">Social&nbsp;=&nbsp;</span>
              <span className="text-paper">100 − (30·crit + 15·high + 5·med)</span>
            </div>
            <div>
              <span className="text-paper-mute">LLMO&nbsp;=&nbsp;</span>
              <span className="text-paper">0.30·CF + 0.25·SoV + 0.25·CA + 0.20·SQ</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
