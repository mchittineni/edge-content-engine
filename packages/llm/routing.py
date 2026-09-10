"""
Model routing matrix for cost-efficient task assignment.
"""

from enum import StrEnum


class TaskTier(StrEnum):
    CLASSIFICATION = "classification"  # Cheap, fast
    SUMMARIZATION = "summarization"  # Cheap, fast
    RESEARCH = "research"  # Strong, high-context
    TECHNICAL_WRITING = "technical_writing"  # Strongest synthesis & tone
    CODE_REVIEW = "code_review"  # Deep reasoning & validation
    SEO = "seo"  # Cheap, fast
    SOCIAL = "social"  # Creative, fast


# Task to model capability mapping
TASK_MODEL_MAPPING: dict[TaskTier, str] = {
    TaskTier.CLASSIFICATION: "gemini-2.0-flash",
    TaskTier.SUMMARIZATION: "gemini-2.0-flash",
    TaskTier.RESEARCH: "gemini-2.0-flash",
    TaskTier.TECHNICAL_WRITING: "gemini-2.0-flash",
    TaskTier.CODE_REVIEW: "gemini-2.0-flash",
    TaskTier.SEO: "gemini-2.0-flash",
    TaskTier.SOCIAL: "gemini-2.0-flash",
}

# Pricing per million tokens (approximate blended estimate for budgeting)
MODEL_PRICING_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}
