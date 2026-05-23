import clsx from "clsx";
import type { Severity } from "@/lib/types";

const MAP: Record<Severity, { label: string; cls: string }> = {
  critical: { label: "CRITICAL", cls: "text-alarm border-alarm/50 bg-alarm/10" },
  high:     { label: "HIGH",     cls: "text-warn  border-warn/50  bg-warn/10"  },
  medium:   { label: "MEDIUM",   cls: "text-cool  border-cool/50  bg-cool/10"  },
  low:      { label: "LOW",      cls: "text-paper-dim border-ink-600 bg-ink-800" },
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const { label, cls } = MAP[severity] ?? MAP.low;
  return (
    <span className={clsx(
      "inline-flex items-center font-mono text-[10px] tracking-terminal px-2 py-0.5 border rounded-sm",
      cls,
    )}>
      {label}
    </span>
  );
}
