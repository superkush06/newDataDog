"use client";
import { useClusters } from "@/hooks/useClusters";
import { ClusterCard } from "@/components/ClusterCard";
import type { Severity } from "@/lib/types";
import { useState } from "react";

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low"];

export default function ClustersPage() {
  const [minSeverity, setMinSeverity] = useState<Severity | "">("");
  const { data, isLoading, error } = useClusters(
    minSeverity ? { min_severity: minSeverity } : undefined
  );

  if (isLoading) return <div className="text-gray-400 text-sm">Loading clusters…</div>;
  if (error || !data) return <div className="text-red-500 text-sm">Failed to load clusters.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Clusters</h1>
        <span className="text-sm text-gray-400">{data.total} total</span>
        <div className="ml-auto flex gap-2">
          <select
            value={minSeverity}
            onChange={(e) => setMinSeverity(e.target.value as Severity | "")}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All severities</option>
            {SEVERITIES.map((s) => (
              <option key={s} value={s} className="capitalize">{s}</option>
            ))}
          </select>
        </div>
      </div>

      {data.clusters.length === 0 ? (
        <p className="text-gray-400 text-sm">No clusters found.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.clusters.map((c) => <ClusterCard key={c.id} cluster={c} />)}
        </div>
      )}
    </div>
  );
}
