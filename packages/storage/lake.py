"""
Content Lake storage abstraction supporting both local filesystem and AWS S3.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from packages.schemas import ArticleRecord


class ContentLake:
    """
    S3 and Local-compatible content store for immutable research,
    drafts, diagrams, and publications.
    """

    def __init__(self, base_dir: Optional[str] = None, s3_bucket: Optional[str] = None):
        self.base_dir = Path(base_dir or os.getenv("CONTENT_DIR", "./content"))
        self.s3_bucket = s3_bucket or os.getenv("S3_CONTENT_BUCKET")
        self.is_s3 = bool(os.getenv("EDGE_ENV") == "prod" and self.s3_bucket)
        
        # Ensure local directories exist
        for subdir in ["raw", "research", "drafts", "diagrams", "published", "analytics", "state"]:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def save_raw(self, source_id: str, content: str, ext: str = "json") -> str:
        path = self.base_dir / "raw" / f"{source_id}.{ext}"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def save_research(self, article_id: str, research_data: Dict[str, Any]) -> str:
        path = self.base_dir / "research" / f"{article_id}_research.json"
        path.write_text(json.dumps(research_data, indent=2, default=str), encoding="utf-8")
        return str(path)

    def save_draft(self, article_id: str, version: int, markdown_text: str) -> str:
        path = self.base_dir / "drafts" / f"{article_id}_v{version}.md"
        path.write_text(markdown_text, encoding="utf-8")
        return str(path)

    def save_diagram(self, article_id: str, filename: str, content: str) -> str:
        path = self.base_dir / "diagrams" / f"{article_id}_{filename}"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def save_article_state(self, article: ArticleRecord) -> str:
        path = self.base_dir / "state" / f"{article.id}.json"
        path.write_text(json.dumps(article.model_dump(), indent=2, default=str), encoding="utf-8")
        return str(path)

    def load_article_state(self, article_id: str) -> Optional[ArticleRecord]:
        path = self.base_dir / "state" / f"{article_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return ArticleRecord.model_validate(data)

    def list_articles(self) -> List[ArticleRecord]:
        state_dir = self.base_dir / "state"
        articles = []
        for file in state_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                articles.append(ArticleRecord.model_validate(data))
            except Exception:
                pass
        return sorted(articles, key=lambda a: a.created_at, reverse=True)


# Singleton instance
default_lake = ContentLake()
