"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchClusters } from "@/lib/api";

export function useClusters(params?: { status?: string; min_severity?: string }) {
  return useQuery({
    queryKey: ["clusters", params],
    queryFn: () => fetchClusters(params),
    refetchInterval: 30_000,
  });
}
