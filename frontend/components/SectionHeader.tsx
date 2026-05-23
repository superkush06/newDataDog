import clsx from "clsx";

/**
 * A horizontal "newsroom byline" section header: a big serif title, a
 * numbered eyebrow on the left, an optional caption that reads like
 * the deck under a print headline, and a rule that fills the rest.
 */
export function SectionHeader({
  eyebrow,
  title,
  caption,
  right,
  tone = "paper",
}: {
  eyebrow?: string;
  title: string;
  caption?: string;
  right?: React.ReactNode;
  tone?: "paper" | "signal";
}) {
  return (
    <div className="mb-6 rise">
      <div className="flex items-baseline gap-4">
        {eyebrow && (
          <span className="font-mono text-[10px] tracking-terminal text-paper-mute mt-2">
            §{eyebrow}
          </span>
        )}
        <h2
          className={clsx(
            "font-display font-bold text-3xl md:text-4xl leading-none tracking-tight",
            tone === "signal" ? "text-signal" : "text-paper",
          )}
        >
          {title}
        </h2>
        <div className="flex-1 border-b rule mb-2" />
        {right}
      </div>
      {caption && (
        <p className="mt-2 text-paper-dim text-sm leading-relaxed max-w-2xl">{caption}</p>
      )}
    </div>
  );
}
