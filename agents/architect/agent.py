"""
Architect Bot: Extracts cloud topologies, generates Mermaid/ASCII diagrams,
and interfaces with tf-arch-diagram-generator.
"""

from typing import Any

from agents.base import BaseAgent
from packages.llm import TaskTier
from packages.schemas import AgentType, ArchitecturePackage


class ArchitectAgent(BaseAgent):
    agent_type = AgentType.ARCHITECT

    async def process(self, article_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        topic = input_payload.get("topic", "")
        research_claims = input_payload.get("claims", [])

        prompt = (
            f"Generate a multi-tier cloud architecture diagram for EDGE:\n"
            f"Topic: {topic}\n"
            f"Claims: {research_claims}\n"
            f"Create valid, renderable Mermaid.js flowchart and ASCII art overview."
        )

        arch_pkg: ArchitecturePackage = await self.llm.generate_structured(
            prompt=prompt,
            response_model=ArchitecturePackage,
            task_tier=TaskTier.TECHNICAL_WRITING,
            agent_name="architect",
        )

        return arch_pkg.model_dump()
