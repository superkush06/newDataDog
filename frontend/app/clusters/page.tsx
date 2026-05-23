"use client";
import { useState } from "react";
import clsx from "clsx";
import { useClusters } from "@/hooks/useClusters";
import { ClusterCard } from "@/components/ClusterCard";
import { SectionHeader } from "@/components/SectionHeader";
import { PageState } from "@/components/PageState";
import type { Severity } from "@/lib/types";

const SEVERITIES: { val: Severity | ""; label: string }[] = [
  { val: "",         label: "all" },
  { val: "critical", label: "critical" },
  { val: "high",     label: "high" },
  { val: "medium",   label: "medium" },
  { val: "low",      label: "low" },
];

export default function ClustersPage() {
  const [minSeverity, setMinSeverity] = useState<Severity | "">("");
  const { data, isLoading, error } = useClusters(
    minSeverity ? { min_severity: minSeverity } : undefined,
  );

  if (isLoading) return <PageState>Loading clusters…</PageState>;
  if (error || !data) return <PageState tone="alarm">Failed to load clusters.</PageState>;

  return (
    <div className="space-y-10">
      <header className="rise">
        <div className="eyebrow mb-2">VOL. 01 · SECTION 04 · CLUSTERS</div>
        <h1 className="font-display font-black text-paper text-5xl md:text-6xl leading-[0.95] tracking-tight">
          Themes in motion
        </h1>
        <p className="mt-3 text-paper-dim max-w-xl">
          Posts grouped by embedding similarity (cosine ≥ 0.82). Each cluster is
          summarized by Groq llama-3.3-70b. Severity scores combine volume,
          engagement, sentiment, velocity, and author influence.
        </p>
      </header>

      <SectionHeader
        eyebrow="01"
        title={`${data.total} active themes`}
        caption="Sorted by severity score. Click any card to see member posts."
        right={
          <div className="flex gap-1 mb-2">
            {SEVERITIES.map((s) => (
              <button
                key={s.val}
                onClick={() => setMinSeverity(s.val)}
                className={clsx(
                  "px-2.5 py-1 font-mono text-[10px] tracking-terminal border transition-colors lowercase",
                  minSeverity === s.val
                    ? "border-signal text-signal bg-signal/10"
                    : "border-ink-600 text-paper-mute hover:border-paper-dim hover:text-paper",
                )}
              >
                {s.label}
              </button>
            ))}
          </div>
        }
      />

      {data.clusters.length === 0 ? (
        <div className="ink-glass rounded-sm p-8 text-center">
          <p className="font-display text-xl text-paper">No clusters yet</p>
          <p className="text-sm text-paper-dim mt-2">
            Cluster runs trigger automatically as new posts are ingested.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.clusters.map((c, i) => (
            <div key={c.id} className="rise" style={{ animationDelay: `${i * 40}ms` }}>
              <ClusterCard cluster={c} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
