"""
Scorer Bot: Evaluates candidate ideas out of 60 points with threshold logic.
"""

from typing import Any, Dict

from agents.base import BaseAgent
from packages.llm import TaskTier
from packages.schemas import AgentType, OpportunityScore


class ScorerAgent(BaseAgent):
    agent_type = AgentType.SCORER

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = input_payload.get("topic", "")
        category = input_payload.get("category", "")
        context = input_payload.get("context", "")

        prompt = (
            f"Score this editorial topic for the EDGE publication:\n"
            f"Topic: {topic}\n"
            f"Category: {category}\n"
            f"Context: {context}\n"
        )

        score: OpportunityScore = await self.llm.generate_structured(
            prompt=prompt,
            response_model=OpportunityScore,
            task_tier=TaskTier.CLASSIFICATION,
            agent_name="scorer",
        )

        return {
            "score": score.model_dump(),
            "total_score": score.total_score,
            "recommendation": score.recommendation,
        }
