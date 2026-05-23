import clsx from "clsx";
import type { Severity } from "@/lib/types";

const MAP: Record<Severity, { label: string; cls: string }> = {
  critical: { label: "Critical", cls: "bg-red-100 text-red-700 ring-red-600/20" },
  high:     { label: "High",     cls: "bg-orange-100 text-orange-700 ring-orange-600/20" },
  medium:   { label: "Medium",   cls: "bg-yellow-100 text-yellow-700 ring-yellow-600/20" },
  low:      { label: "Low",      cls: "bg-gray-100 text-gray-600 ring-gray-500/20" },
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const { label, cls } = MAP[severity] ?? MAP.low;
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset", cls)}>
      {label}
    </span>
  );
}
