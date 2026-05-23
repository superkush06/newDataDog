import { createServer } from "node:http";

const j = (res, data) => {
  res.setHeader("content-type", "application/json");
  res.setHeader("access-control-allow-origin", "*");
  res.end(JSON.stringify(data));
};

const now = new Date().toISOString();
const ago = (min) => new Date(Date.now() - min * 60000).toISOString();

// ── scores ──────────────────────────────────────────────────────────────────
const SCORES = {
  overall: 73, social: 81, llmo: 65,
  social_breakdown: { critical_clusters: 1, high_clusters: 2, medium_clusters: 3 },
  llmo_breakdown: {
    citation_frequency: 60, share_of_voice: 45, citation_accuracy: 78, sentiment_quality: 70,
    per_llm: {
      claude:     { score: 87, mention_rate: 95, avg_position: 1.4, drift: "low" },
      chatgpt:    { score: 61, mention_rate: 80, avg_position: 2.6, drift: "high" },
      gemini:     { score: 78, mention_rate: 90, avg_position: 1.8, drift: "medium" },
      perplexity: { score: 82, mention_rate: 88, avg_position: 1.5, drift: "low" },
    },
  },
  sparklines: { overall: [68,70,71,72,73], social: [78,80,81,81,81], llmo: [58,60,62,64,65] },
};

// ── feed ────────────────────────────────────────────────────────────────────
const POSTS = [
  {
    id: "p1", platform: "x", platform_post_id: "ld-x-001",
    author_handle: "@deathcult_kyle", author_follower_count: 84200,
    text: "@liquiddeathwater three Whole Foods near me are completely out of stock. been out for 2 weeks. what is going on with your supply chain??",
    media_urls: [], likes: 1840, shares: 620, comments: 94,
    permalink: "https://x.com/deathcult_kyle/status/ld-x-001",
    posted_at: ago(180), ingested_at: ago(178), sentiment: "negative", cluster_id: "c1",
  },
  {
    id: "p2", platform: "x", platform_post_id: "ld-x-002",
    author_handle: "@metalpunk_sarah", author_follower_count: 218000,
    text: "the liquid death supply chain is collapsing and nobody is talking about it. 3 distribution centers reportedly paused. batch 24B-11 is the problem. thread 🧵",
    media_urls: [], likes: 4200, shares: 1850, comments: 312,
    permalink: "https://x.com/metalpunk_sarah/status/ld-x-005",
    posted_at: ago(149), ingested_at: ago(147), sentiment: "negative", cluster_id: "c1",
  },
  {
    id: "p3", platform: "x", platform_post_id: "ld-x-003",
    author_handle: "@fitnessfreak_mara", author_follower_count: 12500,
    text: "liquid death cans taste metallic now?? ordered a 12-pack and half of them had this weird aftertaste. switching to something else if this keeps up",
    media_urls: [], likes: 430, shares: 88, comments: 41,
    permalink: "https://x.com/fitnessfreak_mara/status/ld-x-002",
    posted_at: ago(168), ingested_at: ago(166), sentiment: "negative", cluster_id: "c1",
  },
  {
    id: "p4", platform: "reddit", platform_post_id: "ld-r-001",
    author_handle: "u/hydration_nerd", author_follower_count: 0,
    text: "[r/LiquidDeath] PSA: Metallic taste in recent cans — batch 24B-11 confirmed by 40+ commenters. Has anyone contacted Liquid Death support? No response on social yet.",
    media_urls: [], likes: 1120, shares: 0, comments: 214,
    permalink: "https://reddit.com/r/LiquidDeath/comments/ld-r-001",
    posted_at: ago(125), ingested_at: ago(123), sentiment: "negative", cluster_id: "c1",
  },
  {
    id: "p5", platform: "x", platform_post_id: "ld-x-006",
    author_handle: "@concerned_parent_pdx", author_follower_count: 2100,
    text: "My kids drink Liquid Death. The metallic taste has me worried about can lining. Is this a BPA thing? batch 24B-11 recall??",
    media_urls: [], likes: 670, shares: 0, comments: 98,
    permalink: "https://x.com/concerned_parent_pdx/status/ld-x-006",
    posted_at: ago(93), ingested_at: ago(91), sentiment: "negative", cluster_id: "c1",
  },
  {
    id: "p6", platform: "reddit", platform_post_id: "ld-r-002",
    author_handle: "u/former_ld_fan", author_follower_count: 0,
    text: "I reached out to Liquid Death support 5 days ago about the metallic taste. No response. Their Twitter is silent. This is how you lose loyal customers.",
    media_urls: [], likes: 920, shares: 0, comments: 143,
    permalink: "https://reddit.com/r/LiquidDeath/comments/ld-r-004",
    posted_at: ago(80), ingested_at: ago(78), sentiment: "negative", cluster_id: "c1",
  },
  {
    id: "p7", platform: "x", platform_post_id: "ld-x-007",
    author_handle: "@wholesomehike_co", author_follower_count: 5100,
    text: "@liquiddeathwater please explain the metallic can situation. health concern or just bad batch? need to know if i should throw out my supply",
    media_urls: [], likes: 190, shares: 28, comments: 18,
    permalink: "https://x.com/wholesomehike_co/status/ld-x-007",
    posted_at: ago(56), ingested_at: ago(54), sentiment: "question", cluster_id: "c1",
  },
];

const FEED_STATS = {
  volume_24h: 1847,
  sentiment_7d: [
    { date: "05-17", positive: 210, negative: 88,  neutral: 120 },
    { date: "05-18", positive: 198, negative: 102, neutral: 115 },
    { date: "05-19", positive: 225, negative: 91,  neutral: 130 },
    { date: "05-20", positive: 187, negative: 134, neutral: 108 },
    { date: "05-21", positive: 162, negative: 198, neutral: 95  },
    { date: "05-22", positive: 145, negative: 287, neutral: 88  },
    { date: "05-23", positive: 118, negative: 412, neutral: 72  },
  ],
  platform_distribution: { x: 1124, reddit: 512, instagram: 147, tiktok: 64 },
  avg_response_minutes: 0,
};

// ── clusters ─────────────────────────────────────────────────────────────────
const CLUSTERS = [
  {
    id: "c1", brand_id: "brand-ld",
    name: "Metallic taste + stockout — Batch 24B-11",
    summary: "Customers across LA, NYC, and Chicago report a metallic aftertaste in Liquid Death cans from batch 24B-11, coinciding with regional stockouts. No official brand response after 5+ days. A high-follower Twitter thread is amplifying the issue. A concerned parent community segment is raising health-safety framing.",
    post_count: 12, severity: "critical", severity_score: 1140,
    tags: ["metallic-taste", "batch-24B", "stockout", "supply-chain", "health-concern"],
    sentiment_breakdown: { positive: 1, negative: 10, neutral: 0, question: 1 },
    platforms: ["x", "reddit"],
    first_seen_at: ago(180), last_activity_at: ago(12), status: "active",
  },
  {
    id: "c2", brand_id: "brand-ld",
    name: "West Coast stockout — retail",
    summary: "Secondary cluster of stockout-only complaints from LA, SF, and Portland. Separate from the taste issue — customers simply cannot find product on shelves. Whole Foods and Target flagged most.",
    post_count: 6, severity: "high", severity_score: 510,
    tags: ["stockout", "retail", "west-coast"],
    sentiment_breakdown: { positive: 0, negative: 5, neutral: 1, question: 0 },
    platforms: ["x"],
    first_seen_at: ago(240), last_activity_at: ago(45), status: "active",
  },
  {
    id: "c3", brand_id: "brand-ld",
    name: "Sparkling vs still can confusion",
    summary: "Customers receiving sparkling when they ordered still (and vice versa) from Amazon and direct.com. Packaging similarity flagged. Lower severity but growing.",
    post_count: 4, severity: "medium", severity_score: 245,
    tags: ["packaging", "amazon", "fulfillment"],
    sentiment_breakdown: { positive: 0, negative: 2, neutral: 1, question: 1 },
    platforms: ["x", "reddit"],
    first_seen_at: ago(300), last_activity_at: ago(120), status: "active",
  },
];

// ── queue ────────────────────────────────────────────────────────────────────
const QUEUE = CLUSTERS.map(c => ({
  ...c,
  score_breakdown: {
    cluster_id: c.id,
    volume: c.post_count * 10,
    engagement: c.id === "c1" ? 1820 : c.id === "c2" ? 380 : 140,
    sentiment: c.id === "c1" ? 318 : c.id === "c2" ? 145 : 58,
    velocity: c.id === "c1" ? 54.5 : c.id === "c2" ? 22.1 : 8.4,
    influence_multiplier: c.id === "c1" ? 1.5 : 1.0,
    severity_score: c.severity_score,
    severity: c.severity,
    auto_escalate: c.id === "c1",
  },
}));

// ── actions ──────────────────────────────────────────────────────────────────
const ACTIONS = [
  {
    id: "a1", type: "response", state: "pending",
    cluster_id: "c1", target_post_id: "p2",
    draft: {
      text: "We hear you — and we're investigating batch 24B-11 right now. If you got a can that tastes off, email murder@liquiddeath.com with your batch number and we'll make it right. No corporate runaround. Update coming in 24h.",
      char_count: 232, char_limit: 280, platform: "x",
    },
    context: {
      cluster_summary: CLUSTERS[0].summary,
      original_post_text: POSTS[1].text,
      similar_report_count: 12,
    },
    created_at: ago(30),
  },
  {
    id: "a2", type: "ticket", state: "pending",
    cluster_id: "c1",
    draft: {
      title: "[P1] Metallic taste report — Batch 24B-11 can lining investigation",
      description: "12 social reports (X + Reddit) of metallic taste in batch 24B-11 cans. Regional stockouts across LA/NYC/Chicago may indicate a rushed production run. A parent-community segment is raising health-safety framing — potential recall risk if unaddressed. 5-day response gap already visible.",
      priority: "P1 (score: 1140)",
      social_links: POSTS.slice(0, 5).map(p => p.permalink),
    },
    context: { cluster_summary: CLUSTERS[0].summary, similar_report_count: 12 },
    created_at: ago(29),
  },
  {
    id: "a3", type: "escalation", state: "pending",
    cluster_id: "c1",
    draft: {
      channel: "#brand-crisis",
      summary: CLUSTERS[0].summary,
      top_posts: POSTS.slice(0, 5).map(p => p.permalink),
      recommended_actions: [
        "Issue a holding statement on @liquiddeathwater Twitter within 2h",
        "Pull batch 24B-11 from e-commerce fulfillment pending QA review",
        "Open war room with supply chain + QA teams",
      ],
    },
    context: { cluster_summary: CLUSTERS[0].summary, similar_report_count: 12 },
    created_at: ago(28),
  },
  {
    id: "a4", type: "ground_truth_correction", state: "pending",
    cluster_id: "c1",
    draft: {
      llm: "chatgpt",
      ground_truth: "Liquid Death is canned mountain water. It contains zero alcohol, zero caffeine, and zero energy ingredients.",
      llm_claim: "Liquid Death is an energy drink brand popular with extreme sports athletes, known for its high caffeine content and edgy branding.",
      correction: "Liquid Death is 100% mountain water — no caffeine, no alcohol, no energy ingredients. Just water in a can that looks cooler than your ex.",
    },
    context: {
      cluster_summary: "ChatGPT consistently misidentifies Liquid Death as an energy drink across 3 probe runs. Drift score: 0.81.",
      similar_report_count: 3,
    },
    created_at: ago(15),
  },
];

// ── llmo audits ───────────────────────────────────────────────────────────────
const AUDITS = [
  {
    id: "au1", brand_id: "brand-ld", llm: "chatgpt",
    prompt: "What is Liquid Death?",
    prompt_id: "pr1",
    response: "Liquid Death is a popular energy drink brand known for its aggressive marketing targeting extreme sports and heavy metal culture...",
    mentioned: true, position: 1,
    competitors_mentioned: ["PRIME Hydration", "Monster Energy"],
    sentiment: -0.1, claims: ["energy drink", "high caffeine", "extreme sports"],
    drift_score: 0.81, citation_accuracy: 19,
    ingested_at: ago(10),
  },
  {
    id: "au2", brand_id: "brand-ld", llm: "claude",
    prompt: "What is Liquid Death?",
    prompt_id: "pr1",
    response: "Liquid Death is a canned mountain water company known for its irreverent heavy-metal branding. They sell still and sparkling water...",
    mentioned: true, position: 1,
    competitors_mentioned: ["Essentia", "Core Water"],
    sentiment: 0.6, claims: ["canned water", "recyclable aluminum", "mountain water"],
    drift_score: 0.04, citation_accuracy: 96,
    ingested_at: ago(10),
  },
  {
    id: "au3", brand_id: "brand-ld", llm: "gemini",
    prompt: "What is Liquid Death?",
    prompt_id: "pr1",
    response: "Liquid Death is a beverage brand offering canned water and some sparkling options. Their marketing leans heavily on heavy metal aesthetics...",
    mentioned: true, position: 1,
    competitors_mentioned: ["Waterboy", "Cirkul"],
    sentiment: 0.4, claims: ["canned water", "sparkling water", "heavy metal branding"],
    drift_score: 0.12, citation_accuracy: 88,
    ingested_at: ago(10),
  },
  {
    id: "au4", brand_id: "brand-ld", llm: "perplexity",
    prompt: "What is Liquid Death?",
    prompt_id: "pr1",
    response: "Liquid Death is a canned mountain water brand. The company sells still and sparkling water in tallboy aluminum cans with an extreme marketing aesthetic...",
    mentioned: true, position: 1,
    competitors_mentioned: ["PRIME Hydration"],
    sentiment: 0.5, claims: ["mountain water", "aluminum cans", "recyclable"],
    drift_score: 0.08, citation_accuracy: 92,
    ingested_at: ago(10),
  },
  {
    id: "au5", brand_id: "brand-ld", llm: "chatgpt",
    prompt: "Is Liquid Death an energy drink or water?",
    prompt_id: "pr2",
    response: "Liquid Death started as water but has expanded into energy drinks. Many people confuse it with traditional energy drink brands...",
    mentioned: true, position: 1,
    competitors_mentioned: ["Monster Energy", "Red Bull"],
    sentiment: 0.1, claims: ["expanded into energy drinks", "energy drink brand"],
    drift_score: 0.76, citation_accuracy: 24,
    ingested_at: ago(8),
  },
  {
    id: "au6", brand_id: "brand-ld", llm: "claude",
    prompt: "Is Liquid Death an energy drink or water?",
    prompt_id: "pr2",
    response: "Liquid Death is water — specifically canned mountain water. Despite the extreme branding that might suggest an energy drink, it contains zero caffeine and zero alcohol...",
    mentioned: true, position: 1, competitors_mentioned: [],
    sentiment: 0.7, claims: ["water only", "zero caffeine", "zero alcohol"],
    drift_score: 0.02, citation_accuracy: 98,
    ingested_at: ago(8),
  },
];

// ── server ────────────────────────────────────────────────────────────────────
createServer((req, res) => {
  const pathname = req.url?.split("?")[0];

  if (pathname === "/api/scores")       return j(res, SCORES);
  if (pathname === "/api/feed")         return j(res, { posts: POSTS, next_cursor: null, stats: FEED_STATS });
  if (pathname === "/api/clusters")     return j(res, { clusters: CLUSTERS, total: CLUSTERS.length });
  if (pathname === "/api/queue")        return j(res, { queue: QUEUE, threshold_config: { critical: 700, high: 400, medium: 200 }, weights: { volume: 10, like: 2, share: 5, comment: 3, sentiment: 3.5 } });
  if (pathname === "/api/actions")      return j(res, { actions: ACTIONS, total: ACTIONS.length });
  if (pathname === "/api/llmo/audits")  return j(res, { audits: AUDITS });
  if (pathname?.startsWith("/api/llmo/probe")) return j(res, { status: "triggered" });
  if (pathname?.startsWith("/api/actions/") && req.method === "POST") return j(res, { status: "ok" });

  return j(res, { ok: true });
}).listen(8000, () => {
  console.log("✓ Pulse mock server running on http://localhost:8000");
  console.log("  Liquid Death demo data loaded:");
  console.log("  · 7 posts  · 3 clusters (1 Critical)  · 4 actions  · 6 LLMO audits");
});
