"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchScores } from "@/lib/api";

export function useScores() {
  return useQuery({
    queryKey: ["scores"],
    queryFn: fetchScores,
    refetchInterval: 30_000,
  });
}
