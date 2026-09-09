"""
Publisher Bot: Asynchronous publishing downstream to Beehiiv.
Canonical copy remains in PostgreSQL and S3 Lake.
"""

from typing import Any, Dict, Optional

from agents.base import BaseAgent
from packages.beehiiv import BeehiivClient
from packages.schemas import AgentType, ArticleDraft, PublicationRecord


class PublisherAgent(BaseAgent):
    agent_type = AgentType.PUBLISHER

    def __init__(self, beehiiv_client: Optional[BeehiivClient] = None):
        super().__init__()
        self.beehiiv = beehiiv_client or BeehiivClient()

    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        draft_dict = input_payload.get("draft", {})
        draft = ArticleDraft.model_validate(draft_dict)

        # Create asynchronous post draft on Beehiiv
        record: PublicationRecord = await self.beehiiv.create_draft_post(draft)
        return record.model_dump()
