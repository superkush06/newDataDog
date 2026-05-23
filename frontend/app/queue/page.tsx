"use client";
import { useQueue } from "@/hooks/useQueue";
import { QueueTable } from "@/components/QueueTable";
import { SectionHeader } from "@/components/SectionHeader";
import { PageState } from "@/components/PageState";

export default function QueuePage() {
  const { data, isLoading, error } = useQueue();

  if (isLoading) return <PageState>Loading queue…</PageState>;
  if (error || !data) return <PageState tone="alarm">Failed to load queue.</PageState>;

  return (
    <div className="space-y-10">
      <header className="rise">
        <div className="eyebrow mb-2">VOL. 01 · SECTION 05 · TRIAGE</div>
        <h1 className="font-display font-black text-paper text-5xl md:text-6xl leading-[0.95] tracking-tight">
          Priority queue
        </h1>
        <p className="mt-3 text-paper-dim max-w-2xl">
          Active clusters ranked by composite severity score. Volume, engagement,
          sentiment, velocity, and author influence all feed in. Anything above
          the critical threshold auto-enqueues a draft response for human review.
        </p>
      </header>

      <SectionHeader eyebrow="01" title={`${data.queue.length} in queue`} />

      {data.queue.length === 0 ? (
        <div className="ink-glass rounded-sm p-8 text-center">
          <p className="font-display text-xl text-paper">Queue is empty</p>
          <p className="text-sm text-paper-dim mt-2">No active clusters above threshold right now.</p>
        </div>
      ) : (
        <QueueTable
          items={data.queue}
          thresholds={data.threshold_config}
          weights={data.weights}
        />
      )}
    </div>
  );
}
