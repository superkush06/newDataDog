"use client";
import { useQuery } from "@tanstack/react-query";
import { fetchFeed } from "@/lib/api";

export function useFeed() {
  return useQuery({
    queryKey: ["feed"],
    queryFn: () => fetchFeed(),
    refetchInterval: 30_000,
  });
}
