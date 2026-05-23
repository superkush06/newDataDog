"use client";
import { useScores } from "@/hooks/useScores";
import { ScoreHero } from "@/components/ScoreHero";
import { ScoringMethod } from "@/components/ScoringMethod";
import { LLMVisibilityGrid } from "@/components/LLMVisibilityGrid";
import { SectionHeader } from "@/components/SectionHeader";
import { PageState } from "@/components/PageState";
import { XAgentPanel } from "@/components/XAgentPanel";

export default function DashboardPage() {
  const { data, isLoading, error } = useScores();

  if (isLoading) return <PageState>Loading scores…</PageState>;
  if (error || !data)
    return <PageState tone="alarm">Failed to load scores. Is the backend running on :8000?</PageState>;

  const sb = data.social_breakdown ?? { critical_clusters: 0, high_clusters: 0, medium_clusters: 0 };
  const lb = data.llmo_breakdown ?? {
    citation_frequency: 0, share_of_voice: 0, citation_accuracy: 0,
    sentiment_quality: 0, per_llm: {} as Record<string, never>,
  };
  const computedAt = (data as { computed_at?: string }).computed_at;

  const llmoMetrics: { code: string; name: string; value: number }[] = [
    { code: "CF",  name: "Citation Frequency",  value: lb.citation_frequency },
    { code: "SoV", name: "Share of Voice",      value: lb.share_of_voice },
    { code: "CA",  name: "Citation Accuracy",   value: lb.citation_accuracy },
    { code: "SQ",  name: "Sentiment Quality",   value: lb.sentiment_quality },
  ];

  return (
    <div className="space-y-12">
      {/* page header */}
      <header className="flex items-end justify-between gap-6 flex-wrap rise">
        <div>
          <div className="eyebrow mb-2">VOL. 01 · ISSUE 01 · BRAND HEALTH</div>
          <h1 className="font-display font-black text-paper text-5xl md:text-6xl leading-[0.95] tracking-tight">
            The morning brief
          </h1>
          <p className="mt-3 text-paper-dim max-w-xl">
            What the open web and four large language models are saying about your
            brand right now — distilled, scored, and ranked.
          </p>
        </div>
        {computedAt && (
          <div className="text-right">
            <div className="eyebrow text-[10px]">LAST RECOMPUTE</div>
            <div className="num text-paper text-sm mt-1">
              {new Date(computedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </div>
          </div>
        )}
      </header>

      <ScoreHero snapshot={data} />

      {/* Two cards: social pressure + LLMO sub-metrics */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="ink-glass rounded-sm p-6 rise" style={{ animationDelay: "60ms" }}>
          <div className="flex items-baseline justify-between mb-4">
            <h3 className="eyebrow">SOCIAL PRESSURE / 24h</h3>
            <span className="num text-[10px] text-paper-mute">postgres · clusters</span>
          </div>
          <SeverityBar sb={sb} />
          <p className="mt-4 text-[12px] text-paper-dim leading-relaxed">
            Pressure&nbsp;=&nbsp;
            <span className="num text-alarm">{sb.critical_clusters}×30</span>
            &nbsp;+&nbsp;
            <span className="num text-warn">{sb.high_clusters}×15</span>
            &nbsp;+&nbsp;
            <span className="num text-cool">{sb.medium_clusters}×5</span>
            &nbsp;=&nbsp;
            <span className="num text-paper">
              {sb.critical_clusters * 30 + sb.high_clusters * 15 + sb.medium_clusters * 5}
            </span>
            &nbsp;→ Social = {100 - (sb.critical_clusters * 30 + sb.high_clusters * 15 + sb.medium_clusters * 5)}
          </p>
        </div>

        <div className="ink-glass rounded-sm p-6 rise" style={{ animationDelay: "120ms" }}>
          <div className="flex items-baseline justify-between mb-4">
            <h3 className="eyebrow">LLMO SUB-METRICS</h3>
            <span className="num text-[10px] text-paper-mute">clickhouse · llmo_audits</span>
          </div>
          <ul className="space-y-3">
            {llmoMetrics.map((m) => (
              <li key={m.code} className="flex items-center gap-3">
                <span className="num text-[10px] tracking-terminal text-signal w-10">
                  {m.code}
                </span>
                <span className="text-sm text-paper-dim flex-1">{m.name}</span>
                <div className="flex-1 h-1.5 bg-ink-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-signal rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(100, Math.max(0, m.value))}%` }}
                  />
                </div>
                <span className="num text-paper w-12 text-right text-sm">
                  {m.value?.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <ScoringMethod />

      <XAgentPanel />

      <section>
        <SectionHeader
          eyebrow="03"
          title="Per-LLM visibility"
          caption="Same brand, four different models, four different stories. Drift label flags how far each model is from your declared ground-truth."
        />
        <LLMVisibilityGrid perLlm={lb.per_llm as never} />
      </section>
    </div>
  );
}

function SeverityBar({ sb }: { sb: { critical_clusters: number; high_clusters: number; medium_clusters: number } }) {
  const items = [
    { key: "critical", value: sb.critical_clusters, label: "Critical", tone: "bg-alarm",  color: "text-alarm" },
    { key: "high",     value: sb.high_clusters,     label: "High",     tone: "bg-warn",   color: "text-warn"  },
    { key: "medium",   value: sb.medium_clusters,   label: "Medium",   tone: "bg-cool",   color: "text-cool"  },
  ];
  const max = Math.max(1, ...items.map((i) => i.value));
  return (
    <div className="space-y-3">
      {items.map((i) => (
        <div key={i.key} className="flex items-baseline gap-3">
          <span className="text-xs text-paper-dim w-16">{i.label}</span>
          <div className="flex-1 h-7 bg-ink-700 rounded-sm overflow-hidden flex items-center">
            <div
              className={`${i.tone} h-full transition-all duration-700`}
              style={{ width: `${(i.value / max) * 100}%`, minWidth: i.value > 0 ? "8px" : 0 }}
            />
          </div>
          <span className={`num font-bold text-2xl ${i.color} w-10 text-right`}>{i.value}</span>
        </div>
      ))}
    </div>
  );
}
