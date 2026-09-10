"""
Standard JobContract for decoupled, asynchronous agent communication.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(StrEnum):
    DISCOVERY = "discovery"
    SCORER = "scorer"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    WRITER = "writer"
    FACTCHECKER = "factchecker"
    VALIDATOR = "validator"
    SEO = "seo"
    PUBLISHER = "publisher"
    SOCIAL = "social"
    ANALYTICS = "analytics"
    GITHUB_EVENT = "github_event"
    EVERGREEN = "evergreen"


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class JobMetadata(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:12]}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    model_used: str | None = None
    prompt_version: str | None = None
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0


class JobContract(BaseModel):
    """
    Decoupled contract passed through SQS / event bus.
    Every agent consumes and produces this standard structure.
    """

    job_id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    article_id: str
    agent: AgentType
    status: JobStatus = JobStatus.PENDING
    attempt: int = 1
    max_attempts: int = 3
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    metadata: JobMetadata = Field(default_factory=JobMetadata)
