"use client";
import { useState } from "react";
import { useFeed } from "@/hooks/useFeed";
import { useRealtimeFeed } from "@/hooks/useRealtimeFeed";
import { PostCard } from "@/components/PostCard";
import { FeedSidebar } from "@/components/FeedSidebar";
import type { Platform } from "@/lib/types";

const PLATFORMS: Platform[] = ["x", "instagram", "tiktok", "reddit", "facebook"];

export default function FeedPage() {
  useRealtimeFeed();
  const { data, isLoading, error } = useFeed();
  const [platform, setPlatform] = useState<Platform | "all">("all");

  if (isLoading) return <div className="text-gray-400 text-sm">Loading feed…</div>;
  if (error || !data) return <div className="text-red-500 text-sm">Failed to load feed.</div>;

  const posts = platform === "all"
    ? data.posts
    : data.posts.filter((p) => p.platform === platform);

  return (
    <div className="flex gap-8">
      <div className="flex-1 min-w-0 space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <h1 className="text-2xl font-bold text-gray-900 mr-2">Live Feed</h1>
          <button
            onClick={() => setPlatform("all")}
            className={`text-xs px-3 py-1 rounded-full border ${platform === "all" ? "bg-indigo-600 text-white border-indigo-600" : "border-gray-300 text-gray-600 hover:bg-gray-50"}`}
          >
            All
          </button>
          {PLATFORMS.map((p) => (
            <button
              key={p}
              onClick={() => setPlatform(p)}
              className={`text-xs px-3 py-1 rounded-full border capitalize ${platform === p ? "bg-indigo-600 text-white border-indigo-600" : "border-gray-300 text-gray-600 hover:bg-gray-50"}`}
            >
              {p}
            </button>
          ))}
        </div>

        {posts.length === 0 ? (
          <p className="text-gray-400 text-sm">No posts yet. Start the mock server or connect a brand.</p>
        ) : (
          <div className="space-y-3">
            {posts.map((p) => <PostCard key={p.id} post={p} />)}
          </div>
        )}
      </div>

      <FeedSidebar stats={data.stats} />
    </div>
  );
}
