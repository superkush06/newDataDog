import clsx from "clsx";
import type { Post, Sentiment } from "@/lib/types";

const SENTIMENT_BORDER: Record<Sentiment, string> = {
  positive: "border-l-green-500",
  negative: "border-l-red-500",
  neutral:  "border-l-gray-300",
  question: "border-l-blue-400",
};

const PLATFORM_ICON: Record<string, string> = {
  x: "𝕏",
  instagram: "📸",
  tiktok: "🎵",
  reddit: "🔴",
  facebook: "👤",
};

export function PostCard({ post }: { post: Post }) {
  return (
    <div className={clsx("border-l-4 bg-white rounded-r-lg shadow-sm p-4 space-y-2", SENTIMENT_BORDER[post.sentiment])}>
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-800 text-sm">{post.author_handle}</span>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{PLATFORM_ICON[post.platform] ?? post.platform}</span>
          <span>{new Date(post.posted_at).toLocaleString()}</span>
        </div>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed">{post.text}</p>
      <div className="flex gap-4 text-xs text-gray-400">
        <span>❤️ {post.likes}</span>
        <span>🔁 {post.shares}</span>
        <span>💬 {post.comments}</span>
        {post.permalink && (
          <a href={post.permalink} target="_blank" rel="noreferrer" className="ml-auto text-indigo-500 hover:underline">
            View →
          </a>
        )}
      </div>
    </div>
  );
}
