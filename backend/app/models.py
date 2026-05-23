from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Platform = Literal["x", "instagram", "tiktok", "reddit", "facebook"]
Sentiment = Literal["positive", "negative", "neutral", "question"]
Severity = Literal["critical", "high", "medium", "low"]
ClusterStatus = Literal["active", "resolved", "snoozed"]
ActionType = Literal["response", "ticket", "escalation", "faq", "insight", "dm"]
ActionState = Literal["pending", "approved", "executed", "rejected"]
Vertical = Literal["generic", "healthcare"]


class Post(BaseModel):
    id: Optional[str] = None
    brand_id: Optional[str] = None
    platform: Platform
    platform_post_id: str
    author_handle: str
    author_follower_count: int = 0
    text: str
    media_urls: list[str] = []
    likes: int = 0
    shares: int = 0
    comments: int = 0
    permalink: str
    posted_at: datetime
    ingested_at: Optional[datetime] = None
    sentiment: Sentiment = "neutral"
    cluster_id: Optional[str] = None
    source: Literal["webhook", "nimble"] = "webhook"


class SentimentBreakdown(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    question: int = 0


class Cluster(BaseModel):
    id: Optional[str] = None
    brand_id: str
    name: str
    summary: str
    centroid: Optional[list[float]] = None
    post_count: int = 0
    severity: Severity = "low"
    severity_score: float = 0
    tags: list[str] = []
    sentiment_breakdown: SentimentBreakdown = Field(default_factory=SentimentBreakdown)
    platforms: list[Platform] = []
    first_seen_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    status: ClusterStatus = "active"


class ScoreBreakdown(BaseModel):
    cluster_id: str
    volume: float
    engagement: float
    sentiment: float
    velocity: float
    influence_multiplier: float
    severity_score: float
    severity: Severity
    auto_escalate: bool


class ActionContext(BaseModel):
    cluster_summary: str
    original_post_text: Optional[str] = None
    similar_report_count: int = 0


class Action(BaseModel):
    id: Optional[str] = None
    type: ActionType
    state: ActionState = "pending"
    cluster_id: str
    target_post_id: Optional[str] = None
    draft: dict
    context: ActionContext
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    reject_reason: Optional[str] = None
    outcome: Optional[dict] = None


class Brand(BaseModel):
    id: Optional[str] = None
    name: str
    vertical: Vertical = "generic"
    voice_guidelines: str = ""
    keywords: list[str] = []
    thresholds: dict = {"critical": 700, "high": 400, "medium": 200}
    connections: dict = {}


class DecisionBody(BaseModel):
    decision: Literal["approve", "edit_approve", "reject", "reassign"]
    edited_text: Optional[str] = None
    reject_reason: Optional[str] = None
