import clsx from "clsx";

export function LiveDot({
  label,
  tone = "signal",
  size = "sm",
}: {
  label?: string;
  tone?: "signal" | "alarm" | "warn";
  size?: "sm" | "md";
}) {
  const toneCls =
    tone === "alarm" ? "bg-alarm shadow-[0_0_8px_var(--alarm)]"
    : tone === "warn"  ? "bg-warn shadow-[0_0_8px_var(--warn)]"
    : "bg-signal shadow-[0_0_8px_var(--signal)]";
  const dim =
    tone === "alarm" ? "text-alarm" : tone === "warn" ? "text-warn" : "text-signal";

  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={clsx(
          "rounded-full animate-pulse-dot",
          size === "md" ? "w-2.5 h-2.5" : "w-1.5 h-1.5",
          toneCls,
        )}
      />
      {label && (
        <span className={clsx("eyebrow text-[10px]", dim)}>{label}</span>
      )}
    </span>
  );
}
