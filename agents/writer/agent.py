"""
Writer Bot: Senior Technical Editor for EDGE enforcing the 14-section format.
"""

from typing import Any, Dict

from agents.base import BaseAgent
from packages.llm import TaskTier
from packages.schemas import AgentType, ArticleDraft


class WriterAgent(BaseAgent):
    agent_type = AgentType.WRITER

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = input_payload.get("topic", "")
        research = input_payload.get("research", {})
        architecture = input_payload.get("architecture", {})

        prompt = (
            f"Draft the definitive EDGE article for:\n"
            f"Topic: {topic}\n"
            f"Research Evidence: {research}\n"
            f"Architecture Topology: {architecture}\n"
            f"Follow all 14 sections strictly without fluff or filler."
        )

        draft: ArticleDraft = await self.llm.generate_structured(
            prompt=prompt,
            response_model=ArticleDraft,
            task_tier=TaskTier.TECHNICAL_WRITING,
            agent_name="writer",
        )

        return draft.model_dump()
