"use client";
import { useState } from "react";
import clsx from "clsx";
import type { Action } from "@/lib/types";
import { useDecideAction } from "@/hooks/useActions";

function ActionTypePill({ type }: { type: string }) {
  const colors: Record<string, string> = {
    response: "bg-indigo-100 text-indigo-700",
    ticket: "bg-yellow-100 text-yellow-700",
    escalation: "bg-red-100 text-red-700",
    faq: "bg-green-100 text-green-700",
    insight: "bg-purple-100 text-purple-700",
    dm: "bg-blue-100 text-blue-700",
    ground_truth_correction: "bg-rose-100 text-rose-700",
  };
  return (
    <span className={clsx("text-xs font-medium rounded px-2 py-0.5", colors[type] ?? "bg-gray-100 text-gray-600")}>
      {type.replace(/_/g, " ")}
    </span>
  );
}

export function ActionCard({ action }: { action: Action }) {
  const decide = useDecideAction();
  const isGtc = action.type === "ground_truth_correction";
  const draft = action.draft as Record<string, string>;
  const [text, setText] = useState<string>(draft?.text ?? draft?.description ?? "");
  const [editing, setEditing] = useState(false);

  return (
    <div className={clsx("rounded-lg border p-5 space-y-4", isGtc ? "bg-rose-50 border-rose-200" : "bg-white border-gray-100 shadow-sm")}>
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <ActionTypePill type={action.type} />
          <p className="text-xs text-gray-500 line-clamp-2">{action.context.cluster_summary}</p>
        </div>
        <span className="text-xs text-gray-400 shrink-0">{new Date(action.created_at).toLocaleString()}</span>
      </div>

      {isGtc && draft?.ground_truth && (
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="bg-white rounded p-3 border border-rose-200">
            <p className="font-medium text-gray-700 mb-1">Ground Truth</p>
            <p className="text-gray-600">{draft.ground_truth}</p>
          </div>
          <div className="bg-white rounded p-3 border border-rose-200">
            <p className="font-medium text-gray-700 mb-1">LLM Claim ({draft.llm})</p>
            <p className="text-red-600">{draft.llm_claim}</p>
          </div>
        </div>
      )}

      {(draft?.text || draft?.description) && (
        <div>
          {editing ? (
            <textarea
              className="w-full text-sm border border-gray-300 rounded p-2 h-28 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          ) : (
            <p className="text-sm text-gray-700 bg-gray-50 rounded p-3 whitespace-pre-wrap">{text}</p>
          )}
          {draft?.char_limit && (
            <p className="text-right text-xs text-gray-400 mt-1">{text.length}/{draft.char_limit}</p>
          )}
        </div>
      )}

      {action.state === "pending" && (
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (editing) {
                decide.mutate({ id: action.id, decision: "edit_approve", editedText: text });
                setEditing(false);
              } else {
                decide.mutate({ id: action.id, decision: "approve" });
              }
            }}
            className="flex-1 text-sm bg-indigo-600 text-white rounded px-3 py-1.5 hover:bg-indigo-700 disabled:opacity-50"
            disabled={decide.isPending}
          >
            {editing ? "Approve Edits" : "Approve"}
          </button>
          {!editing && (draft?.text || draft?.description) && (
            <button
              onClick={() => setEditing(true)}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 hover:bg-gray-50"
            >
              Edit
            </button>
          )}
          {editing && (
            <button
              onClick={() => setEditing(false)}
              className="text-sm border border-gray-300 rounded px-3 py-1.5 hover:bg-gray-50"
            >
              Cancel
            </button>
          )}
          <button
            onClick={() => decide.mutate({ id: action.id, decision: "reject" })}
            className="text-sm border border-red-300 text-red-600 rounded px-3 py-1.5 hover:bg-red-50 disabled:opacity-50"
            disabled={decide.isPending}
          >
            Reject
          </button>
        </div>
      )}

      {action.state !== "pending" && (
        <p className="text-xs text-gray-400 capitalize">Status: {action.state}</p>
      )}
    </div>
  );
}
