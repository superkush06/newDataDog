"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchActions, decideAction } from "@/lib/api";

export function useActions(params?: { type?: string; state?: string }) {
  return useQuery({
    queryKey: ["actions", params],
    queryFn: () => fetchActions(params),
    refetchInterval: 30_000,
  });
}

export function useDecideAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      decision,
      editedText,
      rejectReason,
    }: {
      id: string;
      decision: "approve" | "edit_approve" | "reject";
      editedText?: string;
      rejectReason?: string;
    }) => decideAction(id, decision, editedText, rejectReason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["actions"] });
    },
  });
}
