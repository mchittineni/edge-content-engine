import pytest
from packages.schemas import OpportunityScore, JobContract, AgentType, JobStatus, ArticleRecord, ArticleStatus


def test_opportunity_scoring_thresholds():
    # High score >= 48 -> RESEARCH_IMMEDIATELY
    high_score = OpportunityScore(
        github_relevance=10,
        originality=9,
        technical_depth=9,
        search_demand=8,
        current_interest=8,
        personal_authority=10,
    )
    assert high_score.total_score == 54
    assert high_score.recommendation == "RESEARCH_IMMEDIATELY"

    # Mid score 40-47 -> BACKLOG
    mid_score = OpportunityScore(
        github_relevance=7,
        originality=7,
        technical_depth=7,
        search_demand=7,
        current_interest=7,
        personal_authority=7,
    )
    assert mid_score.total_score == 42
    assert mid_score.recommendation == "BACKLOG"

    # Low score < 30 -> DISCARD
    low_score = OpportunityScore(
        github_relevance=2,
        originality=3,
        technical_depth=3,
        search_demand=3,
        current_interest=2,
        personal_authority=2,
    )
    assert low_score.total_score == 15
    assert low_score.recommendation == "DISCARD"


def test_job_contract_creation():
    job = JobContract(
        article_id="EDGE-2026-001",
        agent=AgentType.WRITER,
        input_payload={"topic": "Test topic"},
    )
    assert job.status == JobStatus.PENDING
    assert job.attempt == 1
    assert job.metadata.trace_id.startswith("trace_")


def test_article_record_initial_state():
    article = ArticleRecord(
        id="EDGE-2026-001",
        topic="Terraform plans are terrible architecture diagrams",
    )
    assert article.status == ArticleStatus.DISCOVERED
    assert article.revisions_count == 0
