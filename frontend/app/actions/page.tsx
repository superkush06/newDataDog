"use client";
import { useState } from "react";
import clsx from "clsx";
import { useActions } from "@/hooks/useActions";
import { ActionCard } from "@/components/ActionCard";
import { GroundTruthDriftCard } from "@/components/GroundTruthDriftCard";
import { PendingXReplyCard } from "@/components/PendingXReplyCard";
import { SectionHeader } from "@/components/SectionHeader";
import { PageState } from "@/components/PageState";
import type { ActionType } from "@/lib/types";

const TYPES: { val: ActionType | ""; label: string }[] = [
  { val: "",           label: "all" },
  { val: "response",   label: "response" },
  { val: "ticket",     label: "ticket" },
  { val: "escalation", label: "escalation" },
  { val: "ground_truth_correction", label: "correction" },
  { val: "insight",    label: "insight" },
];

const STATES: { val: string; label: string }[] = [
  { val: "pending",  label: "pending" },
  { val: "approved", label: "approved" },
  { val: "executed", label: "executed" },
  { val: "rejected", label: "rejected" },
  { val: "",         label: "all" },
];

export default function ActionsPage() {
  const [typeFilter, setTypeFilter] = useState<ActionType | "">("");
  const [stateFilter, setStateFilter] = useState<string>("pending");

  const { data, isLoading, error } = useActions({
    type: typeFilter || undefined,
    state: stateFilter || undefined,
  });

  if (isLoading) return <PageState>Loading actions…</PageState>;
  if (error || !data) return <PageState tone="alarm">Failed to load actions.</PageState>;

  return (
    <div className="space-y-10">
      <header className="rise">
        <div className="eyebrow mb-2">VOL. 01 · SECTION 06 · ACTIONS</div>
        <h1 className="font-display font-black text-paper text-5xl md:text-6xl leading-[0.95] tracking-tight">
          Drafts awaiting<br />your sign-off
        </h1>
        <p className="mt-3 text-paper-dim max-w-2xl">
          Pulse never posts on your behalf without approval. Every response,
          ticket, escalation, and ground-truth correction lands here first.
        </p>
      </header>

      <SectionHeader
        eyebrow="01"
        title={`${data.total} action${data.total === 1 ? "" : "s"}`}
        caption="Filter by status and type."
        right={
          <div className="flex gap-3 flex-wrap mb-2">
            <Group label="STATE">
              {STATES.map((s) => (
                <Pill key={s.val} active={stateFilter === s.val} onClick={() => setStateFilter(s.val)}>
                  {s.label}
                </Pill>
              ))}
            </Group>
            <Group label="TYPE">
              {TYPES.map((t) => (
                <Pill key={t.val} active={typeFilter === t.val} onClick={() => setTypeFilter(t.val as ActionType | "")}>
                  {t.label}
                </Pill>
              ))}
            </Group>
          </div>
        }
      />

      <div className="space-y-3">
        {/* Demo: live X reply staged by the X monitoring agent. Sits above the
            regular action queue so judges see it first. */}
        {stateFilter === "pending" && (
          <div className="rise"><PendingXReplyCard /></div>
        )}

        {data.actions.length === 0 ? (
          <div className="ink-glass rounded-sm p-8 text-center">
            <p className="font-display text-xl text-paper">No further actions match these filters</p>
          </div>
        ) : (
          data.actions.map((action, i) => (
            <div key={action.id} className="rise" style={{ animationDelay: `${(i + 1) * 40}ms` }}>
              {action.type === "ground_truth_correction" ? (
                <GroundTruthDriftCard action={action} />
              ) : (
                <ActionCard action={action} />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="eyebrow text-[10px]">{label}</span>
      <div className="flex gap-1">{children}</div>
    </div>
  );
}

function Pill({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "px-2.5 py-1 font-mono text-[10px] tracking-terminal border transition-colors lowercase",
        active
          ? "border-signal text-signal bg-signal/10"
          : "border-ink-600 text-paper-mute hover:border-paper-dim hover:text-paper",
      )}
    >
      {children}
    </button>
  );
}
