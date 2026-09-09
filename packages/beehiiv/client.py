"""
Asynchronous Beehiiv API v2 Client.
Handles post creation, asynchronous status polling, and HTML payload conversion.
"""

import asyncio
import os
from typing import Dict, Any, Optional
import httpx
from packages.schemas import ArticleDraft, PublicationRecord


class BeehiivClient:
    """
    Downstream publishing client for Beehiiv.
    The canonical source of truth remains in PostgreSQL & S3 Lake.
    """

    def __init__(self, api_token: Optional[str] = None, publication_id: Optional[str] = None):
        self.api_token = api_token or os.getenv("BEEHIIV_API_TOKEN")
        self.publication_id = publication_id or os.getenv("BEEHIIV_PUBLICATION_ID")
        self.base_url = "https://api.beehiiv.com/v2"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_draft_post(
        self,
        draft: ArticleDraft,
        subtitle: Optional[str] = None,
        author: str = "Manideep Chittineni",
    ) -> PublicationRecord:
        """
        Creates an asynchronous post draft on Beehiiv.
        Polls until the post status transitions from processing (202) to ready.
        """
        if not self.api_token or not self.publication_id:
            # Simulated publication record for local / dev testing
            fake_post_id = f"post_beehiiv_{draft.article_id.lower().replace('-', '_')}"
            return PublicationRecord(
                article_id=draft.article_id,
                platform="beehiiv",
                post_id=fake_post_id,
                web_url=f"https://edge.beehiiv.com/p/{draft.title.lower().replace(' ', '-')}",
                status="draft",
            )

        endpoint = f"{self.base_url}/publications/{self.publication_id}/posts"
        
        # Render markdown content into HTML or Beehiiv post blocks
        payload = {
            "title": draft.title,
            "subtitle": subtitle or draft.thesis,
            "content_tags": ["Architecture", "Platform Engineering", "Cloud", "DevSecOps"],
            "authors": [author],
            "body": draft.full_markdown,
            "status": "draft",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, headers=self._headers(), json=payload)
            
            if response.status_code not in (200, 201, 202):
                raise RuntimeError(
                    f"Beehiiv API Error ({response.status_code}): {response.text}"
                )

            data = response.json().get("data", {})
            post_id = data.get("id")

            # Asynchronous Polling: Beehiiv may return 202 while processing
            record = await self.poll_post_ready(post_id, draft.article_id)
            return record

    async def poll_post_ready(
        self, post_id: str, article_id: str, max_retries: int = 10, delay_sec: float = 2.0
    ) -> PublicationRecord:
        """
        Polls until the post is processed and returns the stable post URL.
        """
        endpoint = f"{self.base_url}/publications/{self.publication_id}/posts/{post_id}"

        for _ in range(max_retries):
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(endpoint, headers=self._headers())
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    web_url = data.get("web_url") or data.get("canonical_url")
                    return PublicationRecord(
                        article_id=article_id,
                        platform="beehiiv",
                        post_id=post_id,
                        web_url=web_url,
                        status="draft",
                    )
            await asyncio.sleep(delay_sec)

        return PublicationRecord(
            article_id=article_id,
            platform="beehiiv",
            post_id=post_id,
            web_url=None,
            status="pending_processing",
        )
