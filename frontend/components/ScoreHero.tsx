"use client";
import { LineChart, Line, ResponsiveContainer, Tooltip } from "recharts";
import clsx from "clsx";
import type { ScoreSnapshot } from "@/lib/types";

function ScoreCard({
  label,
  value,
  delta,
  sparkline,
  size = "normal",
}: {
  label: string;
  value: number;
  delta?: number;
  sparkline?: number[];
  size?: "large" | "normal";
}) {
  const color =
    value >= 70 ? "text-green-600" : value >= 40 ? "text-amber-600" : "text-rose-600";
  const chartColor =
    value >= 70 ? "#16a34a" : value >= 40 ? "#d97706" : "#e11d48";

  const sparkData = (sparkline ?? []).map((v, i) => ({ i, v }));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col gap-3">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">{label}</p>
      <div className="flex items-end gap-3">
        <span className={clsx("font-extrabold leading-none", size === "large" ? "text-6xl" : "text-4xl", color)}>
          {value}
        </span>
        {delta !== undefined && (
          <span className={clsx("text-sm font-medium mb-1", delta >= 0 ? "text-green-500" : "text-red-500")}>
            {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}
          </span>
        )}
      </div>
      {sparkData.length > 1 && (
        <ResponsiveContainer width="100%" height={40}>
          <LineChart data={sparkData}>
            <Tooltip
              contentStyle={{ fontSize: 11, padding: "2px 8px" }}
              formatter={(v: number) => [v, label]}
              labelFormatter={() => ""}
            />
            <Line type="monotone" dataKey="v" stroke={chartColor} dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export function ScoreHero({ snapshot }: { snapshot: ScoreSnapshot }) {
  return (
    <div className="grid grid-cols-3 gap-6">
      <ScoreCard
        label="Overall Brand Health"
        value={snapshot.overall}
        sparkline={snapshot.sparklines?.overall}
        size="large"
      />
      <ScoreCard
        label="Social Score"
        value={snapshot.social}
        sparkline={snapshot.sparklines?.social}
      />
      <ScoreCard
        label="LLMO Score"
        value={snapshot.llmo}
        sparkline={snapshot.sparklines?.llmo}
      />
    </div>
  );
}
