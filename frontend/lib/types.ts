export type Platform = "x" | "instagram" | "tiktok" | "reddit" | "facebook";
export type Sentiment = "positive" | "negative" | "neutral" | "question";
export type Severity = "critical" | "high" | "medium" | "low";
export type ClusterStatus = "active" | "resolved" | "snoozed";
export type ActionType = "response" | "ticket" | "escalation" | "faq" | "insight" | "dm" | "ground_truth_correction";
export type ActionState = "pending" | "approved" | "executed" | "rejected";
export type LLMName = "claude" | "chatgpt" | "gemini" | "perplexity";

export interface Post {
  id: string;
  platform: Platform;
  platform_post_id: string;
  author_handle: string;
  author_follower_count: number;
  text: string;
  media_urls: string[];
  likes: number;
  shares: number;
  comments: number;
  permalink: string;
  posted_at: string;
  ingested_at: string;
  sentiment: Sentiment;
  cluster_id: string | null;
}

export interface SentimentBreakdown {
  positive: number;
  negative: number;
  neutral: number;
  question: number;
}

export interface Cluster {
  id: string;
  brand_id: string;
  name: string;
  summary: string;
  post_count: number;
  severity: Severity;
  severity_score: number;
  tags: string[];
  sentiment_breakdown: SentimentBreakdown;
  platforms: Platform[];
  first_seen_at: string;
  last_activity_at: string;
  status: ClusterStatus;
}

export interface ScoreBreakdown {
  cluster_id: string;
  volume: number;
  engagement: number;
  sentiment: number;
  velocity: number;
  influence_multiplier: number;
  severity_score: number;
  severity: Severity;
  auto_escalate: boolean;
}

export interface QueueItem extends Cluster {
  score_breakdown: ScoreBreakdown;
}

export interface Action {
  id: string;
  type: ActionType;
  state: ActionState;
  cluster_id: string;
  target_post_id?: string;
  draft: Record<string, unknown>;
  context: {
    cluster_summary: string;
    original_post_text?: string;
    similar_report_count: number;
  };
  created_at: string;
  decided_at?: string;
  decided_by?: string;
  reject_reason?: string;
  outcome?: Record<string, unknown>;
}

export interface LLMAudit {
  id: string;
  brand_id: string;
  llm: LLMName;
  prompt: string;
  prompt_id: string;
  response: string;
  mentioned: boolean;
  position: 0 | 1 | 2 | 3 | 4;
  competitors_mentioned: string[];
  sentiment: number;
  claims: string[];
  drift_score: number;
  citation_accuracy: number;
  ingested_at: string;
}

export interface LLMScore {
  score: number;
  mention_rate: number;
  avg_position: number;
  drift: "low" | "medium" | "high";
}

export interface ScoreSnapshot {
  brand_id: string;
  timestamp: string;
  overall: number;
  social: number;
  llmo: number;
  social_breakdown: {
    critical_clusters: number;
    high_clusters: number;
    medium_clusters: number;
    volume_24h?: number;
    negative_pct?: number;
  };
  llmo_breakdown: {
    citation_frequency: number;
    share_of_voice: number;
    citation_accuracy: number;
    sentiment_quality: number;
    per_llm: Record<LLMName, LLMScore>;
  };
  sparklines: {
    overall: number[];
    social: number[];
    llmo: number[];
  };
}

export interface FeedStats {
  volume_24h: number;
  sentiment_7d: { date: string; positive: number; negative: number; neutral: number }[];
  platform_distribution: Partial<Record<Platform, number>>;
  avg_response_minutes: number;
}

export interface FeedResponse {
  posts: Post[];
  next_cursor: string | null;
  stats: FeedStats;
}

export interface ThresholdConfig {
  critical: number;
  high: number;
  medium: number;
}

export interface QueueWeights {
  volume: number;
  like: number;
  share: number;
  comment: number;
  sentiment: number;
}
