"use client";
import { useScores } from "@/hooks/useScores";
import { useLLMOAudits } from "@/hooks/useLLMOAudits";
import { LLMVisibilityGrid } from "@/components/LLMVisibilityGrid";
import { PromptResults } from "@/components/PromptResults";
import { triggerLLMProbe } from "@/lib/api";
import { useState } from "react";
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
      await refetch();
    } finally {
      setProbing(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LLMO — LLM Optimization</h1>
          <p className="text-sm text-gray-500 mt-1">How AI models describe, cite, and position your brand</p>
        </div>
        <button
          onClick={handleProbe}
          disabled={probing}
          className="ml-auto text-sm bg-indigo-600 text-white rounded px-4 py-2 hover:bg-indigo-700 disabled:opacity-50"
        >
          {probing ? "Probing…" : "Probe Now"}
        </button>
      </div>

      {scores?.llmo_breakdown?.per_llm && (
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Per-LLM Grid</h2>
          <LLMVisibilityGrid perLlm={scores.llmo_breakdown.per_llm} />
        </div>
      )}

      <div>
        <div className="flex items-center gap-4 mb-4">
          <h2 className="text-lg font-semibold text-gray-800">Prompt Results</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setLlmFilter("")}
              className={`text-xs px-3 py-1 rounded-full border ${llmFilter === "" ? "bg-indigo-600 text-white border-indigo-600" : "border-gray-300 text-gray-600 hover:bg-gray-50"}`}
            >
              All LLMs
            </button>
            {LLM_NAMES.map((l) => (
              <button
                key={l}
                onClick={() => setLlmFilter(l)}
                className={`text-xs px-3 py-1 rounded-full border capitalize ${llmFilter === l ? "bg-indigo-600 text-white border-indigo-600" : "border-gray-300 text-gray-600 hover:bg-gray-50"}`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
        <PromptResults audits={audits?.audits ?? []} />
      </div>
    </div>
  );
}
