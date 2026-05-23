"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchLLMOAudits } from "@/lib/api";

export function useLLMOAudits(params?: { llm?: string }) {
  return useQuery({
    queryKey: ["llmo-audits", params],
    queryFn: () => fetchLLMOAudits(params),
    refetchInterval: 60_000,
  });
}
