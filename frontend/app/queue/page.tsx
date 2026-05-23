"use client";
import { useQueue } from "@/hooks/useQueue";
import { QueueTable } from "@/components/QueueTable";

export default function QueuePage() {
  const { data, isLoading, error } = useQueue();

  if (isLoading) return <div className="text-gray-400 text-sm">Loading queue…</div>;
  if (error || !data) return <div className="text-red-500 text-sm">Failed to load queue.</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Priority Queue</h1>
        <p className="text-sm text-gray-500 mt-1">Clusters ranked by composite severity score</p>
      </div>

      {data.queue.length === 0 ? (
        <p className="text-gray-400 text-sm">Queue is empty — no active clusters above threshold.</p>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
          <QueueTable
            items={data.queue}
            thresholds={data.threshold_config}
            weights={data.weights}
          />
        </div>
      )}
    </div>
  );
}
