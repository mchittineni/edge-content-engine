"""
Social Distribution Agent: Platform-tailored content packager for LinkedIn, Reddit, and X.
Enforces authentic community discourse rules (strictly no spam or promotional tone).
"""

from typing import Dict, Any
from packages.schemas import AgentType, SocialPackage
from packages.llm import TaskTier
from agents.base import BaseAgent


class SocialAgent(BaseAgent):
    agent_type = AgentType.SOCIAL

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = input_payload.get("draft", {})

        prompt = (
            f"Generate platform-specific distribution packages for this EDGE article:\n"
            f"Title: {draft.get('title')}\n"
            f"Thesis: {draft.get('thesis')}\n"
            f"Key Takeaways: {draft.get('tldr')}\n"
            f"Architecture: {draft.get('architecture_overview')}\n"
            f"Failure Modes: {draft.get('failure_modes')}\n\n"
            f"STRICT RULES:\n"
            f"1. Reddit: Authentic technical problem statement + code/diagram observation + discussion question. NO spam or newsletter promotional links.\n"
            f"2. LinkedIn: Senior engineering leadership perspective with architecture takeaways.\n"
            f"3. X: High-density 3-5 tweet visual thread."
        )

        social_pkg: SocialPackage = await self.llm.generate_structured(
            prompt=prompt,
            response_model=SocialPackage,
            task_tier=TaskTier.SOCIAL,
            agent_name="social",
        )

        return social_pkg.model_dump()
