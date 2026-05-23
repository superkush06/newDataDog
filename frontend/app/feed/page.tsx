"use client";
import { useMemo, useState } from "react";
import { useFeed } from "@/hooks/useFeed";
import { useRealtimeFeed } from "@/hooks/useRealtimeFeed";
import { PostCard } from "@/components/PostCard";
import { FeedSidebar } from "@/components/FeedSidebar";
import { SectionHeader } from "@/components/SectionHeader";
import { PageState } from "@/components/PageState";
import { LiveDot } from "@/components/LiveDot";
import clsx from "clsx";

type Sort = "new" | "top";

function subFromPermalink(permalink: string | undefined): string | null {
  if (!permalink) return null;
  const m = permalink.match(/reddit\.com\/r\/([^/]+)/i);
  return m ? `r/${m[1]}` : null;
}

export default function FeedPage() {
  useRealtimeFeed();
  const { data, isLoading, error } = useFeed();
  const [sub, setSub] = useState<string>("all");
  const [sort, setSort] = useState<Sort>("new");

  // hooks (useMemo) must run unconditionally — keep them above any early return
  const subs = useMemo(() => {
    const set = new Set<string>();
    (data?.posts ?? []).forEach((p) => {
      const s = subFromPermalink(p.permalink);
      if (s) set.add(s);
    });
    return Array.from(set).sort();
  }, [data]);

  const posts = useMemo(() => {
    const list = (data?.posts ?? []).filter((p) => p.platform === "reddit");
    const filtered = sub === "all"
      ? list
      : list.filter((p) => subFromPermalink(p.permalink) === sub);
    return [...filtered].sort((a, b) =>
      sort === "top"
        ? (b.likes + b.comments) - (a.likes + a.comments)
        : new Date(b.posted_at).getTime() - new Date(a.posted_at).getTime(),
    );
  }, [data, sub, sort]);

  if (isLoading) return <PageState>Loading Reddit feed…</PageState>;
  if (error || !data)
    return <PageState tone="alarm">Failed to load feed.</PageState>;

  return (
    <div className="space-y-10">
      <header className="rise">
        <div className="eyebrow mb-2">VOL. 01 · SECTION 02 · LIVE FEED</div>
        <div className="flex items-end justify-between gap-6 flex-wrap">
          <div>
            <h1 className="font-display font-black text-paper text-5xl md:text-6xl leading-[0.95] tracking-tight">
              From the front lines<br />
              <span className="text-reddit">of Reddit</span>
            </h1>
            <p className="mt-3 text-paper-dim max-w-xl">
              Every brand mention our pipeline has surfaced, sentiment-classified
              by Groq, clustered by embedding similarity. Polled every 30 seconds.
            </p>
          </div>
          <div className="ink-glass rounded-sm px-4 py-3 flex items-center gap-3">
            <LiveDot label="STREAMING" />
            <span className="num text-paper-dim text-[11px]">
              source: reddit · adapter: nimble
            </span>
          </div>
        </div>
      </header>

      <div className="flex gap-8">
        <div className="flex-1 min-w-0 space-y-5">
          {/* filter bar */}
          <div className="ink-glass rounded-sm px-4 py-3 flex items-center gap-3 flex-wrap">
            <span className="eyebrow shrink-0">SUB</span>
            <div className="flex gap-1 flex-wrap">
              <Pill active={sub === "all"} onClick={() => setSub("all")}>all</Pill>
              {subs.map((s) => (
                <Pill key={s} active={sub === s} onClick={() => setSub(s)}>{s}</Pill>
              ))}
            </div>
            <div className="ml-auto flex items-center gap-2">
              <span className="eyebrow">SORT</span>
              <Pill active={sort === "new"} onClick={() => setSort("new")}>new</Pill>
              <Pill active={sort === "top"} onClick={() => setSort("top")}>top</Pill>
            </div>
          </div>

          {posts.length === 0 ? (
            <div className="ink-glass rounded-sm p-8 text-center">
              <p className="font-display text-xl text-paper">No reddit posts yet</p>
              <p className="text-sm text-paper-dim mt-2">
                Seed posts via the monitor pipeline or start the Nimble adapter.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {posts.map((p, i) => (
                <div key={p.id} className="rise" style={{ animationDelay: `${i * 30}ms` }}>
                  <PostCard post={p} />
                </div>
              ))}
            </div>
          )}
        </div>

        <FeedSidebar stats={data.stats} posts={data.posts.filter((p) => p.platform === "reddit")} />
      </div>
    </div>
  );
}

function Pill({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "px-2.5 py-1 font-mono text-[10px] tracking-terminal border transition-colors lowercase",
        active
          ? "border-reddit text-reddit bg-reddit/10"
          : "border-ink-600 text-paper-mute hover:border-paper-dim hover:text-paper",
      )}
    >
      {children}
    </button>
  );
}
