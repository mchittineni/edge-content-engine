import pytest
from apps.workers.pipeline import ArticlePipelineOrchestrator
from packages.schemas import ArticleStatus


@pytest.mark.asyncio
async def test_full_pipeline_orchestration():
    orchestrator = ArticlePipelineOrchestrator()
    article = await orchestrator.run_pipeline(
        article_id="EDGE-TEST-001",
        topic="Terraform plans are terrible architecture diagrams",
        category="architecture",
    )

    assert article.status == ArticleStatus.AWAITING_APPROVAL
    assert article.score is not None
    assert article.score.total_score >= 48
    assert article.research is not None
    assert len(article.research.claims) > 0
    assert article.draft is not None
    assert article.qa is not None
    assert article.qa.technical_score >= 90
    assert article.seo is not None
    assert article.social is not None
