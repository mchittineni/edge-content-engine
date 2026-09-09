"""
Researcher Bot: Gathers primary documentation, GitHub evidence, and structured claims.
"""

from typing import Any, Dict

from agents.base import BaseAgent
from packages.llm import TaskTier
from packages.schemas import AgentType, ResearchPackage


class ResearcherAgent(BaseAgent):
    agent_type = AgentType.RESEARCHER

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = input_payload.get("topic", "")
        category = input_payload.get("category", "")

        prompt = (
            f"Conduct rigorous primary technical research for the EDGE article:\n"
            f"Article ID: {article_id}\n"
            f"Topic: {topic}\n"
            f"Category: {category}\n"
            f"Ensure every high-importance claim has a Tier 1 or Tier 2 citation."
        )

        research_pkg: ResearchPackage = await self.llm.generate_structured(
            prompt=prompt,
            response_model=ResearchPackage,
            task_tier=TaskTier.RESEARCH,
            agent_name="researcher",
        )

        return research_pkg.model_dump()
