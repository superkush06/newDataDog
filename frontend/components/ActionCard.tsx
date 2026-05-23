"use client";
import { useState } from "react";
import clsx from "clsx";
import type { Action } from "@/lib/types";
import { useDecideAction } from "@/hooks/useActions";

const TYPE_META: Record<string, { label: string; tone: string }> = {
  response:                { label: "RESPONSE",     tone: "text-signal border-signal/40 bg-signal/5" },
  ticket:                  { label: "TICKET",       tone: "text-warn   border-warn/40   bg-warn/5"   },
  escalation:              { label: "ESCALATION",   tone: "text-alarm  border-alarm/40  bg-alarm/5"  },
  faq:                     { label: "FAQ",          tone: "text-cool   border-cool/40   bg-cool/5"   },
  insight:                 { label: "INSIGHT",      tone: "text-paper  border-ink-600   bg-ink-800/50" },
  dm:                      { label: "DM",           tone: "text-cool   border-cool/40   bg-cool/5"   },
  ground_truth_correction: { label: "CORRECTION",   tone: "text-alarm  border-alarm/40  bg-alarm/5"  },
};

const STATE_META: Record<string, string> = {
  pending:  "text-warn",
  approved: "text-signal",
  executed: "text-signal",
  rejected: "text-paper-mute",
};

export function ActionCard({ action }: { action: Action }) {
  const decide = useDecideAction();
  const meta = TYPE_META[action.type] ?? TYPE_META.insight;
  const draft = action.draft as Record<string, string>;
  const [text, setText] = useState<string>(draft?.text ?? draft?.description ?? "");
  const [editing, setEditing] = useState(false);

  return (
    <article className="ink-glass rounded-sm p-5 space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={clsx("font-mono text-[10px] tracking-terminal px-2 py-0.5 border rounded-sm", meta.tone)}>
              {meta.label}
            </span>
            <span className={clsx("eyebrow text-[10px]", STATE_META[action.state])}>
              · {action.state}
            </span>
          </div>
          <p className="text-sm text-paper-dim line-clamp-2">{action.context.cluster_summary}</p>
        </div>
        <span className="num text-[10px] text-paper-mute shrink-0">
          {new Date(action.created_at).toLocaleString()}
        </span>
      </div>

      {(draft?.text || draft?.description) && (
        <div>
          {editing ? (
            <textarea
              className="w-full text-sm bg-ink-900 border rule rounded-sm p-3 h-28 text-paper focus:outline-none focus:border-signal"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          ) : (
            <div className="bg-ink-900/60 rounded-sm p-3 border rule">
              <p className="text-sm text-paper leading-relaxed whitespace-pre-wrap">{text}</p>
            </div>
          )}
          {draft?.char_limit && (
            <p className="text-right num text-[11px] text-paper-mute mt-1">
              {text.length}/{draft.char_limit}
            </p>
          )}
        </div>
      )}

      {action.state === "pending" && (
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => {
              if (editing) {
                decide.mutate({ id: action.id, decision: "edit_approve", editedText: text });
                setEditing(false);
              } else {
                decide.mutate({ id: action.id, decision: "approve" });
              }
            }}
            className="flex-1 font-mono text-[11px] tracking-terminal bg-signal text-ink-950 px-4 py-2 hover:bg-signal/80 disabled:opacity-50"
            disabled={decide.isPending}
          >
            {editing ? "✓ APPROVE EDITS" : "✓ APPROVE"}
          </button>
          {!editing && (draft?.text || draft?.description) && (
            <button
              onClick={() => setEditing(true)}
              className="font-mono text-[11px] tracking-terminal border border-paper-mute text-paper px-4 py-2 hover:border-paper hover:bg-ink-800"
            >
              EDIT
            </button>
          )}
          {editing && (
            <button
              onClick={() => setEditing(false)}
              className="font-mono text-[11px] tracking-terminal border border-paper-mute text-paper px-4 py-2 hover:border-paper hover:bg-ink-800"
            >
              CANCEL
            </button>
          )}
          <button
            onClick={() => decide.mutate({ id: action.id, decision: "reject" })}
            className="font-mono text-[11px] tracking-terminal border border-alarm/50 text-alarm px-4 py-2 hover:bg-alarm hover:text-ink-950"
            disabled={decide.isPending}
          >
            ✗ REJECT
          </button>
        </div>
      )}
    </article>
  );
}
