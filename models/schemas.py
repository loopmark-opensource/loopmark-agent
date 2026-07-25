from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Complaints
# ──────────────────────────────────────────────

class ComplaintSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintCategory(str, Enum):
    PRODUCT = "product"
    SHIPPING = "shipping"
    BILLING = "billing"
    CUSTOMER_SERVICE = "customer_service"
    OTHER = "other"


class Complaint(BaseModel):
    id: str = Field(default_factory=lambda: f"CMP-{int(datetime.utcnow().timestamp())}")
    customer_name: str = ""
    customer_email: str = ""
    message: str
    category: ComplaintCategory = ComplaintCategory.OTHER
    severity: ComplaintSeverity = ComplaintSeverity.MEDIUM
    resolved: bool = False
    response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComplaintAnalysis(BaseModel):
    complaint_id: str
    category: ComplaintCategory
    severity: ComplaintSeverity
    summary: str
    suggested_response: str
    escalate: bool = False
    escalation_reason: Optional[str] = None


# ──────────────────────────────────────────────
# Content / Posting
# ──────────────────────────────────────────────

class Platform(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    BLOG = "blog"
    EMAIL = "email"


class ContentTone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    INSPIRATIONAL = "inspirational"
    URGENT = "urgent"


class PostRequest(BaseModel):
    topic: str
    platform: Platform
    tone: ContentTone = ContentTone.PROFESSIONAL
    target_audience: str = "general audience"
    business_goals: str = ""
    audience_engagement: str = ""
    keywords: list[str] = Field(default_factory=list)
    include_cta: bool = True
    max_length: Optional[int] = None


class GeneratedPost(BaseModel):
    platform: Platform
    content: str
    hashtags: list[str] = Field(default_factory=list)
    character_count: int = 0
    estimated_engagement: str = ""
    best_post_time: str = ""


class ContentCalendarEntry(BaseModel):
    date: str
    platform: Platform
    topic: str
    content: str
    status: str = "scheduled"


# ──────────────────────────────────────────────
# Audience research
# ──────────────────────────────────────────────

class BusinessProfile(BaseModel):
    product_name: str = ""
    tagline: str = ""
    description: str = ""
    target_audience: str = ""
    brand_tone: str = ""
    website_url: str = ""
    default_cta: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AudiencePersona(BaseModel):
    id: str = Field(default_factory=lambda: f"PERSONA-{int(datetime.utcnow().timestamp())}")
    name: str
    demographics: str = ""
    pain_points: str = ""
    goals: str = ""
    preferred_platforms: list[str] = Field(default_factory=list)
    messaging_angles: list[str] = Field(default_factory=list)
    source: str = ""  # e.g. website, crm, manual
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CRMContact(BaseModel):
    segment: str = "general"
    name: str = ""
    email: str = ""
    company: str = ""
    industry: str = ""
    job_title: str = ""
    tags: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Funnel
# ──────────────────────────────────────────────

class FunnelStage(str, Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"
    RETENTION = "retention"
    ADVOCACY = "advocacy"


class Lead(BaseModel):
    id: str = Field(default_factory=lambda: f"LEAD-{int(datetime.utcnow().timestamp())}")
    name: str
    email: str
    company: str = ""
    stage: FunnelStage = FunnelStage.AWARENESS
    score: int = Field(default=0, ge=0, le=100)
    source: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_contacted: Optional[datetime] = None


class LeadAnalysis(BaseModel):
    lead_id: str
    current_stage: FunnelStage
    recommended_next_stage: FunnelStage
    score: int
    next_action: str
    nurture_sequence: list[str]
    estimated_conversion_probability: float = Field(ge=0.0, le=1.0)


class FunnelMetrics(BaseModel):
    total_leads: int = 0
    by_stage: dict[str, int] = Field(default_factory=dict)
    avg_score: float = 0.0
    conversion_rate: float = 0.0
    top_sources: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Agent state (shared graph state)
# ──────────────────────────────────────────────

class AgentIntent(str, Enum):
    COMPLAINT = "complaint"
    POSTING = "posting"
    FUNNEL = "funnel"
    UNKNOWN = "unknown"


class MarketingAgentState(BaseModel):
    """Shared state passed through the LangGraph graph."""
    user_input: str = ""
    intent: AgentIntent = AgentIntent.UNKNOWN
    messages: list[dict] = Field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
