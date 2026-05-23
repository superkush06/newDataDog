"use client";
import type { Action } from "@/lib/types";
import { useDecideAction } from "@/hooks/useActions";

export function GroundTruthDriftCard({ action }: { action: Action }) {
  const decide = useDecideAction();
  const draft = action.draft as Record<string, string>;

  return (
    <div className="bg-rose-50 rounded-xl border-2 border-rose-300 p-6 space-y-4">
      <div className="flex items-center gap-2">
        <span className="inline-block bg-rose-600 text-white text-xs font-bold rounded px-2 py-0.5">
          DRIFT DETECTED
        </span>
        <span className="text-sm font-medium text-rose-800 capitalize">{draft?.llm} — ground truth correction</span>
        <span className="ml-auto text-xs text-rose-400">{new Date(action.created_at).toLocaleString()}</span>
      </div>

      <p className="text-xs text-rose-600">{action.context.cluster_summary}</p>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-lg p-4 border border-rose-200">
          <p className="text-xs font-semibold text-gray-500 mb-2">Ground Truth</p>
          <p className="text-sm text-gray-800">{draft?.ground_truth ?? "—"}</p>
        </div>
        <div className="bg-white rounded-lg p-4 border border-rose-300">
          <p className="text-xs font-semibold text-rose-500 mb-2">
            {draft?.llm ? `${draft.llm}'s Claim` : "LLM Claim"}
          </p>
          <p className="text-sm text-rose-700">{draft?.llm_claim ?? "—"}</p>
        </div>
      </div>

      {draft?.correction && (
        <div className="bg-white rounded-lg p-4 border border-indigo-200">
          <p className="text-xs font-semibold text-indigo-600 mb-2">Drafted Correction</p>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{draft.correction}</p>
        </div>
      )}

      {action.state === "pending" && (
        <div className="flex gap-2">
          <button
            onClick={() => decide.mutate({ id: action.id, decision: "approve" })}
            className="flex-1 bg-rose-600 text-white text-sm rounded px-4 py-2 hover:bg-rose-700 disabled:opacity-50"
            disabled={decide.isPending}
          >
            Approve &amp; Post Correction
          </button>
          <button
            onClick={() => decide.mutate({ id: action.id, decision: "reject" })}
            className="text-sm border border-rose-300 text-rose-600 rounded px-4 py-2 hover:bg-rose-50"
            disabled={decide.isPending}
          >
            Reject
          </button>
        </div>
      )}
    </div>
  );
}
