import clsx from "clsx";
import { LiveDot } from "./LiveDot";

/**
 * Empty/loading/error state matching the editorial-terminal aesthetic.
 * Used wherever a page would otherwise render only "Loading…" plain text.
 */
export function PageState({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "alarm";
}) {
  return (
    <div className={clsx(
      "ink-glass rounded-sm px-6 py-12 flex flex-col items-center text-center gap-3 max-w-xl mx-auto rise",
    )}>
      <LiveDot tone={tone === "alarm" ? "alarm" : "warn"} label={tone === "alarm" ? "ERROR" : "STANDBY"} />
      <p className={clsx(
        "font-display text-xl",
        tone === "alarm" ? "text-alarm" : "text-paper",
      )}>
        {children}
      </p>
      <p className="eyebrow text-[10px] text-paper-mute">
        if this persists, check the backend at <span className="text-paper">localhost:8000/api/health</span>
      </p>
    </div>
  );
}
