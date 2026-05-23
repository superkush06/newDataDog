"use client";
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { subscribeToFeed } from "@/lib/realtime";

export function useRealtimeFeed() {
  const qc = useQueryClient();
  useEffect(() => subscribeToFeed(qc), [qc]);
}
