"""
SEO Bot: High-intent titles, meta descriptions, slugs, keywords, and OpenGraph tags.
"""

from typing import Any, Dict

from agents.base import BaseAgent
from packages.llm import TaskTier
from packages.schemas import AgentType, SEOBundle


class SEOAgent(BaseAgent):
    agent_type = AgentType.SEO

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = input_payload.get("draft", {})

        prompt = (
            f"Generate an optimized SEO and OpenGraph bundle for this EDGE article:\n"
            f"Title: {draft.get('title')}\n"
            f"Thesis: {draft.get('thesis')}\n"
            f"TL;DR: {draft.get('tldr')}\n"
            f"Generate technical search keywords, clean slug, and FAQ."
        )

        seo_bundle: SEOBundle = await self.llm.generate_structured(
            prompt=prompt,
            response_model=SEOBundle,
            task_tier=TaskTier.SEO,
            agent_name="seo",
        )

        return seo_bundle.model_dump()
