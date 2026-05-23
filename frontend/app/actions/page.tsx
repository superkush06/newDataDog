"use client";
import { useActions } from "@/hooks/useActions";
import { ActionCard } from "@/components/ActionCard";
import { GroundTruthDriftCard } from "@/components/GroundTruthDriftCard";
import type { ActionType } from "@/lib/types";
import { useState } from "react";

const TYPES: ActionType[] = ["response", "ticket", "escalation", "faq", "insight", "dm", "ground_truth_correction"];

export default function ActionsPage() {
  const [typeFilter, setTypeFilter] = useState<ActionType | "">("");
  const [stateFilter, setStateFilter] = useState<string>("pending");

  const { data, isLoading, error } = useActions({
    type: typeFilter || undefined,
    state: stateFilter || undefined,
  });

  if (isLoading) return <div className="text-gray-400 text-sm">Loading actions…</div>;
  if (error || !data) return <div className="text-red-500 text-sm">Failed to load actions.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 flex-wrap">
        <h1 className="text-2xl font-bold text-gray-900">Actions</h1>
        <span className="text-sm text-gray-400">{data.total} total</span>

        <div className="ml-auto flex gap-2">
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All states</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="executed">Executed</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ActionType | "")}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All types</option>
            {TYPES.map((t) => (
              <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>
      </div>

      {data.actions.length === 0 ? (
        <p className="text-gray-400 text-sm">No actions found.</p>
      ) : (
        <div className="space-y-4">
          {data.actions.map((action) =>
            action.type === "ground_truth_correction" ? (
              <GroundTruthDriftCard key={action.id} action={action} />
            ) : (
              <ActionCard key={action.id} action={action} />
            )
          )}
        </div>
      )}
    </div>
  );
}
