"""
Fact-Checker Bot: Technical QA verifying citations, AWS/Terraform claims, and accuracy.
"""

from typing import Any, Dict

from agents.base import BaseAgent
from packages.llm import TaskTier
from packages.schemas import AgentType, QAReport


class FactCheckerAgent(BaseAgent):
    agent_type = AgentType.FACTCHECKER

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = input_payload.get("draft", {})
        research = input_payload.get("research", {})

        prompt = (
            f"Perform a strict technical QA review for EDGE article:\n"
            f"Draft Title: {draft.get('title')}\n"
            f"Draft Body: {draft.get('full_markdown')}\n"
            f"Research Evidence: {research}\n"
            f"Verify that claims have supporting evidence and code blocks are realistic."
        )

        qa_report: QAReport = await self.llm.generate_structured(
            prompt=prompt,
            response_model=QAReport,
            task_tier=TaskTier.CODE_REVIEW,
            agent_name="factchecker",
        )

        return qa_report.model_dump()
