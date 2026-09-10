"""
Shared pytest fixtures and test harness configuration for EDGE Content Engine.
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from packages.schemas import (
    AgentType,
    ArticleDraft,
    ArticleRecord,
    ArticleStatus,
    JobContract,
    JobStatus,
    OpportunityScore,
)
from packages.storage import default_lake
from packages.storage.lake import ContentLake


@pytest.fixture(autouse=True)
def isolated_test_env(monkeypatch: pytest.MonkeyPatch) -> Generator[str, None, None]:
    """
    Ensures tests execute with safe test environment variables and an isolated
    temporary storage directory so that test runs never pollute content/ or call live APIs.
    """
    original_base_dir = default_lake.base_dir
    temp_dir = tempfile.mkdtemp(prefix="edge_test_lake_")

    # `default_lake` is a singleton built at import time, rooted at ./content.
    # Modules bind their own reference to that one object, so replacing the
    # name in each module is unreliable - but repointing the shared object's
    # base_dir reaches every holder at once. Without this, agents reached
    # through the pipeline write real files into the repository's content/.
    default_lake.base_dir = Path(temp_dir)
    for subdir in ["raw", "research", "drafts", "diagrams", "published", "analytics", "state"]:
        (default_lake.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("EDGE_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{temp_dir}/edge_test.db")
    monkeypatch.setenv("S3_CONTENT_BUCKET", "mock-test-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("MAX_LLM_COST_PER_ARTICLE", "2.50")
    monkeypatch.setenv("AUTO_RESEARCH_SCORE_THRESHOLD", "48")

    yield temp_dir

    default_lake.base_dir = original_base_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_lake(isolated_test_env: str) -> ContentLake:
    """Provides a ContentLake instance rooted in an isolated temporary directory."""
    return ContentLake(base_dir=isolated_test_env)


@pytest.fixture
def sample_opportunity_score() -> OpportunityScore:
    """Fixture providing a sample OpportunityScore above the threshold."""
    return OpportunityScore(
        github_relevance=9,
        originality=8,
        technical_depth=9,
        search_demand=8,
        current_interest=8,
        personal_authority=9,
    )


@pytest.fixture
def sample_article_record() -> ArticleRecord:
    """Fixture providing an initial ArticleRecord."""
    return ArticleRecord(
        id="EDGE-TEST-001",
        topic="Automating Content Engine with Multi-Agent Systems",
        category="architecture",
        status=ArticleStatus.DISCOVERED,
    )


@pytest.fixture
def sample_job_contract() -> JobContract:
    """Fixture providing a sample JobContract for testing."""
    return JobContract(
        article_id="EDGE-TEST-001",
        agent=AgentType.WRITER,
        input_payload={"topic": "Test topic", "category": "architecture"},
        status=JobStatus.PENDING,
    )


@pytest.fixture
def sample_article_draft() -> ArticleDraft:
    """Fixture providing a fully populated ArticleDraft."""
    return ArticleDraft(
        article_id="EDGE-TEST-001",
        title="Test Post",
        thesis="Terraform plans make poor architecture diagrams.",
        tldr="Plans describe deltas, not topology.",
        why_it_matters="Reviewers approve changes they cannot picture.",
        architecture_overview="Event-driven multi-agent pipeline.",
        how_it_works="Agents consume JobContracts from a queue.",
        implementation_guide="Run `edge pipeline run`.",
        failure_modes="Budget exhaustion and provider timeouts.",
        security_considerations="Path traversal defence in the content lake.",
        cost_analysis="Tracked per article by ArticleBudgetTracker.",
        tradeoffs="Latency versus model quality.",
        what_i_would_build="A topology-first diff renderer.",
        conclusion="Diagram the system, not the diff.",
        full_markdown="# Body",
    )
