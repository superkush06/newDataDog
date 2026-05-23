"use client";
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import type { FeedStats } from "@/lib/types";

export function FeedSidebar({ stats }: { stats: FeedStats }) {
  return (
    <aside className="w-72 shrink-0 space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-4">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Volume (24h)</p>
        <p className="text-3xl font-bold text-gray-900 mt-1">{stats.volume_24h.toLocaleString()}</p>
      </div>

      {stats.sentiment_7d.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Sentiment (7d)</p>
          <ResponsiveContainer width="100%" height={80}>
            <LineChart data={stats.sentiment_7d}>
              <XAxis dataKey="date" hide />
              <Tooltip contentStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="positive" stroke="#22c55e" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="negative" stroke="#ef4444" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {Object.keys(stats.platform_distribution).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Platforms</p>
          <ul className="space-y-1">
            {Object.entries(stats.platform_distribution).map(([p, n]) => (
              <li key={p} className="flex justify-between text-sm">
                <span className="capitalize text-gray-600">{p}</span>
                <span className="font-medium text-gray-800">{n}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-4">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Avg. Response</p>
        <p className="text-2xl font-bold text-gray-900 mt-1">
          {stats.avg_response_minutes > 0 ? `${stats.avg_response_minutes}m` : "—"}
        </p>
      </div>
    </aside>
  );
}
