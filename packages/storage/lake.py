"""
Content Lake storage abstraction supporting both local filesystem and AWS S3.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from packages.schemas import ArticleRecord

logger = logging.getLogger(__name__)


class ContentLake:
    """
    S3 and Local-compatible content store for immutable research,
    drafts, diagrams, and publications.
    """

    def __init__(self, base_dir: str | None = None, s3_bucket: str | None = None):
        dir_str = base_dir or os.getenv("CONTENT_DIR") or "./content"
        self.base_dir = Path(dir_str)
        self.s3_bucket = s3_bucket or os.getenv("S3_CONTENT_BUCKET")
        self.is_s3 = bool(os.getenv("EDGE_ENV") == "prod" and self.s3_bucket)

        # Ensure local directories exist
        for subdir in ["raw", "research", "drafts", "diagrams", "published", "analytics", "state"]:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, subdir: str, filename: str) -> Path:
        """
        Validates and safely resolves path to prevent directory traversal (CWE-22 / CWE-73).
        """
        clean_filename = os.path.basename(filename)
        if clean_filename != filename or not re.match(r"^[a-zA-Z0-9_\-\.]+$", clean_filename):
            raise ValueError(f"Invalid or unsafe filename: {filename}")

        target_dir = os.path.abspath(os.path.join(str(self.base_dir), subdir))
        target_path = os.path.abspath(os.path.join(target_dir, clean_filename))

        if not target_path.startswith(target_dir + os.sep) and target_path != target_dir:
            raise ValueError(f"Path traversal detected: {filename}")

        return Path(target_path)

    def save_raw(self, source_id: str, content: str, ext: str = "json") -> str:
        path = self._resolve_safe_path("raw", f"{source_id}.{ext}")
        path.write_text(content, encoding="utf-8")
        return str(path)

    def save_research(self, article_id: str, research_data: dict[str, Any]) -> str:
        path = self._resolve_safe_path("research", f"{article_id}_research.json")
        path.write_text(json.dumps(research_data, indent=2, default=str), encoding="utf-8")
        return str(path)

    def save_draft(self, article_id: str, version: int, markdown_text: str) -> str:
        path = self._resolve_safe_path("drafts", f"{article_id}_v{version}.md")
        path.write_text(markdown_text, encoding="utf-8")
        return str(path)

    def save_diagram(self, article_id: str, filename: str, content: str) -> str:
        path = self._resolve_safe_path("diagrams", f"{article_id}_{filename}")
        path.write_text(content, encoding="utf-8")
        return str(path)

    def save_article_state(self, article: ArticleRecord) -> str:
        path = self._resolve_safe_path("state", f"{article.id}.json")
        path.write_text(json.dumps(article.model_dump(), indent=2, default=str), encoding="utf-8")
        return str(path)

    def load_article_state(self, article_id: str) -> ArticleRecord | None:
        state_dir = (self.base_dir / "state").resolve()
        for file_path in state_dir.glob("*.json"):
            if file_path.stem == article_id:
                try:
                    with file_path.open(encoding="utf-8") as f:
                        data = json.load(f)
                    return ArticleRecord.model_validate(data)
                except (OSError, json.JSONDecodeError, ValueError):
                    # ValueError covers pydantic ValidationError.
                    logger.warning("Corrupt or unreadable state file: %s", file_path, exc_info=True)
                    return None
        return None

    def list_articles(self) -> list[ArticleRecord]:
        state_dir = self.base_dir / "state"
        articles = []
        for file in state_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                articles.append(ArticleRecord.model_validate(data))
            except (OSError, json.JSONDecodeError, ValueError):
                # Skip corrupt records rather than failing the whole listing.
                logger.warning("Skipping corrupt state file: %s", file, exc_info=True)
        return sorted(articles, key=lambda a: a.created_at, reverse=True)


# Singleton instance
default_lake = ContentLake()
