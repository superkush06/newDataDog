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

export function PromptResults({ audits }: { audits: LLMAudit[] }) {
  const byPrompt: Record<string, LLMAudit[]> = {};
  for (const a of audits) {
    (byPrompt[a.prompt] ??= []).push(a);
  }

  if (Object.keys(byPrompt).length === 0) {
    return <p className="text-sm text-gray-400">No audit results yet.</p>;
  }

  return (
    <div className="space-y-6">
      {Object.entries(byPrompt).map(([prompt, rows]) => {
        const byLlm: Record<string, LLMAudit[]> = {};
        for (const r of rows) (byLlm[r.llm] ??= []).push(r);

        return (
          <div key={prompt} className="bg-white rounded-lg border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-700 italic">&ldquo;{prompt}&rdquo;</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-500">
                    <th className="px-4 py-2 text-left">LLM</th>
                    <th className="px-4 py-2 text-center">Mentioned</th>
                    <th className="px-4 py-2 text-center">Position</th>
                    <th className="px-4 py-2 text-center">Accuracy</th>
                    <th className="px-4 py-2 text-center">Drift</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {LLM_NAMES.map((llm) => {
                    const a = byLlm[llm]?.[0];
                    if (!a) {
                      return (
                        <tr key={llm} className="text-gray-300">
                          <td className="px-4 py-2 capitalize font-medium">{llm}</td>
                          <td colSpan={4} className="px-4 py-2 text-center">no data</td>
                        </tr>
                      );
                    }
                    return (
                      <tr key={llm} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium capitalize text-gray-800">{llm}</td>
                        <td className="px-4 py-2 text-center">
                          {a.mentioned ? (
                            <span className="text-green-600">✓</span>
                          ) : (
                            <span className="text-red-500">✗</span>
                          )}
                        </td>
                        <td className="px-4 py-2 text-center text-gray-600">
                          {POSITION_LABEL[a.position] ?? a.position}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span className={clsx(a.citation_accuracy >= 70 ? "text-green-600" : a.citation_accuracy >= 40 ? "text-amber-600" : "text-red-600")}>
                            {a.citation_accuracy.toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span className={clsx(a.drift_score < 0.3 ? "text-green-600" : a.drift_score < 0.6 ? "text-amber-600" : "text-red-600")}>
                            {(a.drift_score * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
