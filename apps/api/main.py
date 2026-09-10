"""
FastAPI Server for EDGE Content Engine.
Handles GitHub webhooks, article lifecycle queries, and review actions.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi import Path as FPath
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.github import GitHubEventNormalizer
from packages.schemas import ArticleRecord, ArticleStatus
from packages.storage import default_lake

app = FastAPI(
    title="EDGE Content Engine API",
    version="1.0.0",
    description="Event-driven orchestration & review API for EDGE / Beehiiv",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "edge-content-engine"}


@app.get("/api/v1/articles", response_model=list[ArticleRecord])
async def list_articles() -> list[ArticleRecord]:
    return default_lake.list_articles()


@app.get("/api/v1/articles/{article_id}", response_model=ArticleRecord)
async def get_article(article_id: str = FPath(pattern=r"^[a-zA-Z0-9_\-]+$")) -> ArticleRecord:
    article = default_lake.load_article_state(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


class ApprovalActionRequest(BaseModel):
    action: str  # approve | request_changes | reject
    feedback: str | None = None


@app.post("/api/v1/articles/{article_id}/review")
async def review_article(
    body: ApprovalActionRequest, article_id: str = FPath(pattern=r"^[a-zA-Z0-9_\-]+$")
) -> dict[str, str]:
    article = default_lake.load_article_state(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if body.action == "approve":
        article.status = ArticleStatus.APPROVED
    elif body.action == "request_changes":
        article.status = ArticleStatus.CHANGES_REQUESTED
        article.revisions_count += 1
    elif body.action == "reject":
        article.status = ArticleStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    default_lake.save_article_state(article)
    return {"status": "success", "article_id": article_id, "new_state": article.status.value}


@app.post("/api/v1/webhooks/github")
async def github_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    normalizer = GitHubEventNormalizer()
    event = normalizer.normalize(payload.get("action", "push"), payload)
    return {
        "received": True,
        "is_interesting": event.is_interesting,
        "headline": event.headline,
        "rationale": event.rationale,
    }
