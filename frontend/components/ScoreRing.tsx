"use client";
import clsx from "clsx";
import { useEffect, useState } from "react";

/**
 * A radial score "ring" + giant Fraunces number. Pure CSS conic-gradient,
 * animates from 0 → value on mount using the @property --ring-pct trick
 * (see globals.css).
 */
export function ScoreRing({
  value,
  size = 220,
  label,
  caption,
}: {
  value: number;
  size?: number;
  label?: string;
  caption?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const tone =
    clamped >= 70 ? "text-signal"
    : clamped >= 40 ? "text-warn"
    : "text-alarm";

  // animate from 0 → value
  const [pct, setPct] = useState(0);
  useEffect(() => {
    const id = window.setTimeout(() => setPct(clamped), 60);
    return () => window.clearTimeout(id);
  }, [clamped]);

  return (
    <div className="relative flex flex-col items-center" style={{ width: size }}>
      <div
        className={clsx("score-ring rounded-full grid place-items-center", tone)}
        style={{
          width: size,
          height: size,
          ["--ring-pct" as string]: pct,
        }}
      >
        <div
          className="bg-ink-950 rounded-full grid place-items-center"
          style={{ width: size - 16, height: size - 16 }}
        >
          <div className="text-center px-4">
            <div className={clsx("font-display font-black leading-none", tone)}
                 style={{ fontSize: size * 0.36 }}>
              {clamped.toFixed(0)}
            </div>
            {label && (
              <div className="eyebrow mt-2 text-[10px]">{label}</div>
            )}
          </div>
        </div>
      </div>
      {caption && (
        <p className="mt-3 num text-[11px] text-paper-mute">{caption}</p>
      )}
    </div>
  );
}
