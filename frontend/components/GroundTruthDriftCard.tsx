"use client";
import type { Action } from "@/lib/types";
import { useDecideAction } from "@/hooks/useActions";
import { LiveDot } from "./LiveDot";

export function GroundTruthDriftCard({ action }: { action: Action }) {
  const decide = useDecideAction();
  const draft = action.draft as Record<string, string>;

  return (
    <article className="rounded-sm border-2 border-alarm bg-alarm/5 p-6 space-y-5 alarm-glow">
      <div className="flex items-center gap-3 flex-wrap">
        <LiveDot label="DRIFT DETECTED" tone="alarm" size="md" />
        <span className="font-display font-bold text-alarm capitalize">
          {draft?.llm ?? "an LLM"} is misrepresenting the brand
        </span>
        <span className="ml-auto num text-[10px] text-paper-mute">
          {new Date(action.created_at).toLocaleString()}
        </span>
      </div>

      <p className="text-sm text-paper-dim">{action.context.cluster_summary}</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-ink-900 rounded-sm p-4 border rule">
          <div className="eyebrow mb-2 text-signal">GROUND TRUTH</div>
          <p className="text-sm text-paper leading-relaxed">{draft?.ground_truth ?? "—"}</p>
        </div>
        <div className="bg-ink-900 rounded-sm p-4 border border-alarm/40">
          <div className="eyebrow mb-2 text-alarm">
            {draft?.llm ? `${draft.llm.toUpperCase()} CLAIMED` : "LLM CLAIM"}
          </div>
          <p className="text-sm text-alarm leading-relaxed">{draft?.llm_claim ?? "—"}</p>
        </div>
      </div>

      {draft?.correction && (
        <div className="bg-ink-900 rounded-sm p-4 border border-signal/40">
          <div className="eyebrow mb-2 text-signal">DRAFTED CORRECTION</div>
          <p className="text-sm text-paper whitespace-pre-wrap leading-relaxed">{draft.correction}</p>
        </div>
      )}

      {action.state === "pending" && (
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => decide.mutate({ id: action.id, decision: "approve" })}
            className="flex-1 font-mono text-[11px] tracking-terminal bg-alarm text-ink-950 px-4 py-2 hover:bg-alarm/80 disabled:opacity-50"
            disabled={decide.isPending}
          >
            ✓ APPROVE &amp; POST CORRECTION
          </button>
          <button
            onClick={() => decide.mutate({ id: action.id, decision: "reject" })}
            className="font-mono text-[11px] tracking-terminal border border-alarm/50 text-alarm px-4 py-2 hover:bg-alarm/10"
            disabled={decide.isPending}
          >
            ✗ REJECT
          </button>
        </div>
      )}
    </article>
  );
}
