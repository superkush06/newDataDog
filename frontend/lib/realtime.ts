import { createClient } from "@supabase/supabase-js";
import type { QueryClient } from "@tanstack/react-query";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";
const BRAND_ID = process.env.NEXT_PUBLIC_DEMO_BRAND_ID ?? "";

let supabase: ReturnType<typeof createClient> | null = null;

function getSupabase() {
  if (!supabase && SUPABASE_URL && SUPABASE_ANON) {
    supabase = createClient(SUPABASE_URL, SUPABASE_ANON);
  }
  return supabase;
}

export function subscribeToFeed(queryClient: QueryClient) {
  const client = getSupabase();
  if (!client || !BRAND_ID) return () => {};

  const channel = client
    .channel(`feed:${BRAND_ID}`)
    .on("broadcast", { event: "new_post" }, () => {
      queryClient.invalidateQueries({ queryKey: ["feed"] });
    })
    .on("broadcast", { event: "cluster_update" }, () => {
      queryClient.invalidateQueries({ queryKey: ["clusters"] });
      queryClient.invalidateQueries({ queryKey: ["queue"] });
    })
    .on("broadcast", { event: "action_created" }, () => {
      queryClient.invalidateQueries({ queryKey: ["actions"] });
    })
    .subscribe();

  return () => {
    client.removeChannel(channel);
  };
}
