"""
Core Pydantic data models for the EDGE editorial pipeline.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ArticleStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    SCORED = "SCORED"
    RESEARCHING = "RESEARCHING"
    RESEARCHED = "RESEARCHED"
    DRAFTING = "DRAFTING"
    DRAFTED = "DRAFTED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    SEO_READY = "SEO_READY"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    ANALYSING = "ANALYSING"


class SourceTier(StrEnum):
    TIER_1_OFFICIAL = "Tier 1: Official docs, GitHub repos, RFCs, specs, academic papers"
    TIER_2_ENGINEERING_BLOG = "Tier 2: Tech company engineering blogs, conference talks"
    TIER_3_COMMUNITY = "Tier 3: Reddit, Hacker News, community discussions"
    TIER_4_AI = "Tier 4: AI summaries, secondary commentary"


class OpportunityScore(BaseModel):
    github_relevance: int = Field(
        ge=1, le=10, description="Alignment with your repositories & expertise"
    )
    originality: int = Field(ge=1, le=10, description="Uniqueness compared to existing content")
    technical_depth: int = Field(
        ge=1, le=10, description="Opportunity for hands-on, architectural analysis"
    )
    search_demand: int = Field(
        ge=1, le=10, description="Organic search volume & developer curiosity"
    )
    current_interest: int = Field(ge=1, le=10, description="Trending in HN, Reddit, tech feeds")
    personal_authority: int = Field(
        ge=1, le=10, description="Your background in IaC/DevOps/Security"
    )

    @property
    def total_score(self) -> int:
        return (
            self.github_relevance
            + self.originality
            + self.technical_depth
            + self.search_demand
            + self.current_interest
            + self.personal_authority
        )

    @property
    def recommendation(self) -> str:
        score = self.total_score
        if score >= 48:
            return "RESEARCH_IMMEDIATELY"
        if score >= 40:
            return "BACKLOG"
        if score >= 30:
            return "MONITOR"
        return "DISCARD"


class SourceReference(BaseModel):
    title: str
    url: str
    tier: SourceTier
    notes: str | None = None


class ClaimEvidence(BaseModel):
    claim: str
    importance: str = Field(default="high", description="high | medium | low")
    tier: SourceTier = SourceTier.TIER_1_OFFICIAL
    source_name: str
    source_url: str
    quote_or_context: str
    confidence: float = 1.0


class ResearchPackage(BaseModel):
    article_id: str
    topic: str
    thesis: str
    claims: list[ClaimEvidence] = Field(default_factory=list)
    competitors_or_alternatives: list[str] = Field(default_factory=list)
    github_evidence: list[dict[str, Any]] = Field(default_factory=list)
    counterarguments: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)


class ArchitecturePackage(BaseModel):
    article_id: str
    diagram_title: str
    mermaid_code: str
    ascii_art: str | None = None
    svg_path: str | None = None
    png_path: str | None = None
    components: list[dict[str, str]] = Field(default_factory=list)
    tf_plan_insights: dict[str, Any] | None = None


class ArticleDraft(BaseModel):
    article_id: str
    version: int = 1
    title: str
    thesis: str
    tldr: str
    why_it_matters: str
    architecture_overview: str
    how_it_works: str
    implementation_guide: str
    failure_modes: str
    security_considerations: str
    cost_analysis: str
    tradeoffs: str
    what_i_would_build: str
    github_project_links: list[str] = Field(default_factory=list)
    conclusion: str
    full_markdown: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CodeValidationCheck(BaseModel):
    tool: str  # terraform, ruff, tsc, checkov, tflint
    passed: bool
    details: str
    command_run: str | None = None


class QAReport(BaseModel):
    article_id: str
    technical_score: int = Field(ge=0, le=100)
    citation_score: int = Field(ge=0, le=100)
    code_validity_score: int = Field(ge=0, le=100)
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    verified_claims_count: int = 0
    code_checks: list[CodeValidationCheck] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.technical_score >= 90
            and len(self.blocking_issues) == 0
            and all(
                check.passed for check in self.code_checks if check.tool in ["terraform", "ruff"]
            )
        )


class SEOBundle(BaseModel):
    article_id: str
    seo_title: str
    meta_description: str
    slug: str
    primary_keyword: str
    secondary_keywords: list[str] = Field(default_factory=list)
    faq: list[dict[str, str]] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)
    og_title: str
    og_description: str


class SocialPackage(BaseModel):
    article_id: str
    linkedin_post: str
    reddit_post: dict[str, str] = Field(
        description="Keys: title, body, discussion_prompt, target_subreddits"
    )
    x_thread: list[str] = Field(default_factory=list)
    hacker_news_submission: dict[str, str] | None = None


class PublicationRecord(BaseModel):
    article_id: str
    platform: str = "beehiiv"
    post_id: str
    web_url: str | None = None
    status: str = "draft"  # draft | scheduled | published
    published_at: datetime | None = None


class ArticleRecord(BaseModel):
    id: str  # e.g. EDGE-2026-001
    topic: str
    category: str = "architecture"
    status: ArticleStatus = ArticleStatus.DISCOVERED
    score: OpportunityScore | None = None
    research: ResearchPackage | None = None
    architecture: ArchitecturePackage | None = None
    draft: ArticleDraft | None = None
    qa: QAReport | None = None
    seo: SEOBundle | None = None
    social: SocialPackage | None = None
    publication: PublicationRecord | None = None
    revisions_count: int = 0
    total_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
