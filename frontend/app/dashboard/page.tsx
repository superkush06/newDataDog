"use client";
import { useScores } from "@/hooks/useScores";
import { ScoreHero } from "@/components/ScoreHero";
import { LLMVisibilityGrid } from "@/components/LLMVisibilityGrid";

export default function DashboardPage() {
  const { data, isLoading, error } = useScores();

  if (isLoading) return <div className="text-gray-400 text-sm">Loading scores…</div>;
  if (error || !data) return <div className="text-red-500 text-sm">Failed to load scores.</div>;

  const { social_breakdown: sb, llmo_breakdown: lb } = data;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Brand Health Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Overall composite · Social · LLMO</p>
      </div>

      <ScoreHero snapshot={data} />

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-100 shadow-sm p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Social Pressure (24h)</p>
          <ul className="space-y-1 text-sm">
            <li className="flex justify-between">
              <span className="text-red-600">Critical clusters</span>
              <span className="font-semibold">{sb.critical_clusters}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-orange-600">High clusters</span>
              <span className="font-semibold">{sb.high_clusters}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-yellow-600">Medium clusters</span>
              <span className="font-semibold">{sb.medium_clusters}</span>
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-lg border border-gray-100 shadow-sm p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">LLMO Breakdown</p>
          <ul className="space-y-1 text-sm">
            <li className="flex justify-between">
              <span className="text-gray-600">Citation Frequency</span>
              <span className="font-semibold">{lb.citation_frequency}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-600">Share of Voice</span>
              <span className="font-semibold">{lb.share_of_voice}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-600">Citation Accuracy</span>
              <span className="font-semibold">{lb.citation_accuracy}</span>
            </li>
            <li className="flex justify-between">
              <span className="text-gray-600">Sentiment Quality</span>
              <span className="font-semibold">{lb.sentiment_quality}</span>
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-lg border border-gray-100 shadow-sm p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Formula</p>
          <p className="text-xs text-gray-500 leading-relaxed">
            Overall = 0.5 × Social + 0.5 × LLMO<br />
            Social = 100 − severity pressure<br />
            LLMO = 0.30·CitFreq + 0.25·SoV + 0.25·CitAcc + 0.20·SentQ
          </p>
        </div>
      </div>

      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Per-LLM Visibility</h2>
        <LLMVisibilityGrid perLlm={lb.per_llm} />
      </div>
    </div>
  );
}
