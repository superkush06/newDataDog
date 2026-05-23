"use client";
import { useState } from "react";
import clsx from "clsx";
import type { LLMAudit, LLMName } from "@/lib/types";

const POSITION_LABEL: Record<number, string> = {
  0: "—",
  1: "P1 headline",
  2: "P2 early",
  3: "P3 body",
  4: "P4 list",
};

const LLM_NAMES: LLMName[] = ["claude", "chatgpt", "gemini", "perplexity"];

const LLM_DOT: Record<LLMName, string> = {
  claude: "#D88A4E",
  chatgpt: "#5BC59F",
  gemini: "#7CC8FF",
  perplexity: "#B89CE0",
};

function tone(value: number, hi: number, mid: number) {
  return value >= hi ? "text-signal" : value >= mid ? "text-warn" : "text-alarm";
}

/**
 * Per-prompt accordion: each prompt expands to show all 4 LLMs' raw
 * responses + extracted claims, with a compact metric row at the top.
 * The point is to make the audit auditable — you can click and read
 * exactly what the LLM said about you.
 */
export function PromptResults({ audits }: { audits: LLMAudit[] }) {
  const byPrompt: Record<string, LLMAudit[]> = {};
  for (const a of audits) (byPrompt[a.prompt] ??= []).push(a);

  if (Object.keys(byPrompt).length === 0) {
    return (
      <div className="ink-glass rounded-sm p-8 text-center">
        <p className="font-display text-xl text-paper">No audit results yet</p>
        <p className="text-sm text-paper-dim mt-2">
          Hit <span className="text-signal">RUN PROBE</span> to send your prompts to all four LLMs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {Object.entries(byPrompt).map(([prompt, rows], idx) => (
        <PromptRow key={prompt} prompt={prompt} rows={rows} idx={idx} />
      ))}
    </div>
  );
}

function PromptRow({ prompt, rows, idx }: { prompt: string; rows: LLMAudit[]; idx: number }) {
  const [expanded, setExpanded] = useState<LLMName | null>(null);
  const byLlm: Partial<Record<LLMName, LLMAudit>> = {};
  for (const r of rows) byLlm[r.llm] = r;

  const mentionCount = LLM_NAMES.filter((l) => byLlm[l]?.mentioned).length;

  return (
    <div className="ink-glass rounded-sm overflow-hidden rise" style={{ animationDelay: `${idx * 60}ms` }}>
      {/* prompt header */}
      <div className="px-5 py-4 border-b rule flex items-baseline gap-4 bg-ink-900/60">
        <span className="num text-[10px] text-paper-mute">PROMPT #{idx + 1}</span>
        <p className="font-display text-paper text-lg italic flex-1">&ldquo;{prompt}&rdquo;</p>
        <span className="eyebrow text-[10px]">
          <span className={mentionCount === 4 ? "text-signal" : mentionCount === 0 ? "text-alarm" : "text-warn"}>
            {mentionCount}/4
          </span>
          &nbsp;mentioned
        </span>
      </div>

      {/* per-LLM rows */}
      <div className="divide-y rule">
        {LLM_NAMES.map((llm) => {
          const a = byLlm[llm];
          const isOpen = expanded === llm;
          if (!a) {
            return (
              <div key={llm} className="px-5 py-3 flex items-center text-paper-mute text-sm">
                <span
                  className="w-2 h-2 rounded-full mr-3"
                  style={{ background: LLM_DOT[llm], opacity: 0.3 }}
                />
                <span className="capitalize w-24 num text-xs">{llm}</span>
                <span className="text-xs">no data</span>
              </div>
            );
          }
          return (
            <div key={llm}>
              <button
                onClick={() => setExpanded(isOpen ? null : llm)}
                className={clsx(
                  "w-full px-5 py-3 flex items-center gap-3 text-left transition-colors",
                  isOpen ? "bg-ink-800/80" : "hover:bg-ink-800/40",
                )}
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ background: LLM_DOT[llm], boxShadow: `0 0 6px ${LLM_DOT[llm]}` }}
                />
                <span className="font-display font-semibold capitalize text-paper w-24">{llm}</span>
                <span className={clsx("text-sm w-16 num", a.mentioned ? "text-signal" : "text-alarm")}>
                  {a.mentioned ? "✓ cited" : "✗ absent"}
                </span>
                <span className="num text-xs text-paper-dim w-24">
                  {POSITION_LABEL[a.position] ?? a.position}
                </span>
                <div className="flex items-center gap-1.5 w-32">
                  <span className="text-[10px] text-paper-mute eyebrow">ACC</span>
                  <span className={clsx("num text-sm", tone(a.citation_accuracy, 70, 40))}>
                    {a.citation_accuracy.toFixed(0)}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 w-32">
                  <span className="text-[10px] text-paper-mute eyebrow">DRIFT</span>
                  <span className={clsx("num text-sm", tone((1 - a.drift_score) * 100, 70, 40))}>
                    {(a.drift_score * 100).toFixed(0)}%
                  </span>
                </div>
                <span className="ml-auto eyebrow text-[10px] text-paper-mute">
                  {isOpen ? "− collapse" : "+ read response"}
                </span>
              </button>

              {isOpen && (
                <div className="px-5 py-5 bg-ink-900/40 border-t rule space-y-4">
                  {a.competitors_mentioned?.length > 0 && (
                    <div>
                      <div className="eyebrow mb-2">COMPETITORS MENTIONED</div>
                      <div className="flex flex-wrap gap-1.5">
                        {a.competitors_mentioned.map((c) => (
                          <span
                            key={c}
                            className="px-2 py-0.5 text-xs border rule text-paper bg-ink-800 rounded-sm"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {a.claims?.length > 0 && (
                    <div>
                      <div className="eyebrow mb-2">CLAIMS EXTRACTED</div>
                      <ul className="space-y-1.5">
                        {a.claims.map((c, i) => (
                          <li key={i} className="text-sm text-paper-dim leading-snug pl-3 border-l rule">
                            {c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <div className="eyebrow mb-2">FULL RESPONSE</div>
                    <p className="text-sm text-paper-dim whitespace-pre-wrap leading-relaxed font-body">
                      {a.response}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
