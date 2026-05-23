"use client";
import { useState } from "react";
import clsx from "clsx";
import { useScores } from "@/hooks/useScores";
import { useLLMOAudits } from "@/hooks/useLLMOAudits";
import { LLMVisibilityGrid } from "@/components/LLMVisibilityGrid";
import { PromptResults } from "@/components/PromptResults";
import { SectionHeader } from "@/components/SectionHeader";
import { triggerLLMProbe } from "@/lib/api";
import type { LLMName } from "@/lib/types";

const LLM_NAMES: LLMName[] = ["claude", "chatgpt", "gemini", "perplexity"];

export default function LLMOPage() {
  const { data: scores } = useScores();
  const [llmFilter, setLlmFilter] = useState<LLMName | "">("");
  const [probing, setProbing] = useState(false);
  const { data: audits, refetch } = useLLMOAudits(llmFilter ? { llm: llmFilter } : undefined);

  async function handleProbe() {
    setProbing(true);
    try {
      await triggerLLMProbe();
      // give the worker some headroom — Groq TPM-paced probe takes ~30-60s
      await new Promise((r) => setTimeout(r, 1500));
      await refetch();
    } finally {
      setProbing(false);
    }
  }

  const perLlm = scores?.llmo_breakdown?.per_llm;
  const auditCount = audits?.audits?.length ?? 0;

  return (
    <div className="space-y-12">
      <header className="flex items-end justify-between gap-6 flex-wrap rise">
        <div>
          <div className="eyebrow mb-2">VOL. 01 · SECTION 03 · LLMO</div>
          <h1 className="font-display font-black text-paper text-5xl md:text-6xl leading-[0.95] tracking-tight">
            What four AIs<br />say about you
          </h1>
          <p className="mt-4 text-paper-dim max-w-xl leading-relaxed">
            We run your seeded prompts through Claude, ChatGPT, Gemini, and
            Perplexity. A judge model scores each response against your declared
            ground-truth. Drift, citation rank, and competitor crowd-out all flow
            into your LLMO score.
          </p>
        </div>
        <button
          onClick={handleProbe}
          disabled={probing}
          className={clsx(
            "group relative px-5 py-3 font-mono text-xs tracking-terminal border transition-all",
            "border-signal text-signal hover:bg-signal hover:text-ink-950",
            "disabled:opacity-50 disabled:cursor-wait",
          )}
        >
          <span className="absolute inset-0 signal-glow opacity-40 group-hover:opacity-100 transition-opacity pointer-events-none" />
          {probing ? "← PROBING…" : "▶ RUN PROBE"}
        </button>
      </header>

      {perLlm && Object.keys(perLlm).length > 0 ? (
        <section>
          <SectionHeader
            eyebrow="01"
            title="Per-LLM visibility"
            caption="Same brand, four models. Where each one places you, how often it mentions you, and how far it drifts from your ground truth."
          />
          <LLMVisibilityGrid perLlm={perLlm} />
        </section>
      ) : (
        <div className="ink-glass rounded-sm p-8 text-center">
          <p className="font-display text-xl text-paper">No LLMO data for this brand yet</p>
          <p className="text-sm text-paper-dim mt-2">
            Click <span className="text-signal">RUN PROBE</span> to send your prompts to all four LLMs (~60 seconds).
          </p>
        </div>
      )}

      <section>
        <SectionHeader
          eyebrow="02"
          title="Prompt-by-prompt audit"
          caption={`${auditCount} response${auditCount === 1 ? "" : "s"} in the last 24h. Click any row to read the full LLM response, the claims it made, and which competitors it referenced.`}
          right={
            <div className="flex gap-1 mb-2">
              <FilterPill active={llmFilter === ""} onClick={() => setLlmFilter("")}>ALL</FilterPill>
              {LLM_NAMES.map((l) => (
                <FilterPill key={l} active={llmFilter === l} onClick={() => setLlmFilter(l)}>
                  {l.toUpperCase()}
                </FilterPill>
              ))}
            </div>
          }
        />
        <PromptResults audits={audits?.audits ?? []} />
      </section>
    </div>
  );
}

function FilterPill({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "px-2.5 py-1 font-mono text-[10px] tracking-terminal border transition-colors",
        active
          ? "border-signal text-signal bg-signal/10"
          : "border-ink-600 text-paper-mute hover:border-paper-dim hover:text-paper",
      )}
    >
      {children}
    </button>
  );
}
