import clsx from "clsx";
import type { Post, Sentiment } from "@/lib/types";

const SENTIMENT_TAG: Record<Sentiment, { label: string; cls: string }> = {
  positive: { label: "POSITIVE", cls: "text-signal border-signal/40 bg-signal/5" },
  negative: { label: "NEGATIVE", cls: "text-alarm border-alarm/40 bg-alarm/5" },
  neutral:  { label: "NEUTRAL",  cls: "text-paper-dim border-ink-600 bg-ink-800/50" },
  question: { label: "QUESTION", cls: "text-cool border-cool/40 bg-cool/5" },
};

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60)   return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function subFromPermalink(permalink: string | undefined): string | null {
  if (!permalink) return null;
  // https://reddit.com/r/foo/comments/... → r/foo
  const m = permalink.match(/reddit\.com\/r\/([^/]+)/i);
  return m ? `r/${m[1]}` : null;
}

export function PostCard({ post }: { post: Post }) {
  const tag = SENTIMENT_TAG[post.sentiment];
  const sub = subFromPermalink(post.permalink);

  return (
    <article className="ink-glass rounded-sm overflow-hidden group hover:border-paper-mute transition-colors">
      <div className="flex">
        {/* upvote rail (Reddit-flavored) */}
        <div className="w-12 shrink-0 bg-ink-900/60 border-r rule flex flex-col items-center py-3 gap-1">
          <span className="text-reddit text-sm">▲</span>
          <span className="num text-xs text-paper">{post.likes.toLocaleString()}</span>
          <span className="text-paper-mute text-sm opacity-40">▼</span>
        </div>

        {/* body */}
        <div className="flex-1 min-w-0 px-5 py-4 space-y-2">
          <div className="flex items-baseline gap-2 text-[11px] num text-paper-mute flex-wrap">
            {sub && (
              <span className="text-reddit font-semibold">{sub}</span>
            )}
            <span>·</span>
            <span>{post.author_handle}</span>
            <span>·</span>
            <span>{timeAgo(post.posted_at)}</span>
            {post.author_follower_count > 0 && (
              <>
                <span>·</span>
                <span>{post.author_follower_count.toLocaleString()} karma</span>
              </>
            )}
            <span className={clsx(
              "ml-auto eyebrow text-[9px] px-1.5 py-0.5 border rounded-sm",
              tag.cls,
            )}>
              {tag.label}
            </span>
          </div>

          <p className="text-paper text-[15px] leading-relaxed text-pretty">{post.text}</p>

          <div className="flex items-center gap-4 text-[11px] num text-paper-mute pt-1">
            <span>💬 {post.comments.toLocaleString()} comments</span>
            <span>🔁 {post.shares.toLocaleString()} crossposts</span>
            {post.permalink && (
              <a
                href={post.permalink}
                target="_blank"
                rel="noreferrer"
                className="ml-auto text-paper-dim hover:text-signal transition-colors"
              >
                open on reddit →
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
