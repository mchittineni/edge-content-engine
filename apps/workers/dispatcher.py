"""
Agent Dispatcher: Routes JobContract messages to the corresponding agent instance.
"""

from typing import Dict, Type
from packages.schemas import AgentType, JobContract
from agents import (
    BaseAgent,
    DiscoveryAgent,
    ScorerAgent,
    ResearcherAgent,
    ArchitectAgent,
    WriterAgent,
    FactCheckerAgent,
    ValidatorAgent,
    SEOAgent,
    PublisherAgent,
    SocialAgent,
    AnalyticsAgent,
    EvergreenAgent,
)


class AgentDispatcher:
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.DISCOVERY: DiscoveryAgent(),
            AgentType.SCORER: ScorerAgent(),
            AgentType.RESEARCHER: ResearcherAgent(),
            AgentType.ARCHITECT: ArchitectAgent(),
            AgentType.WRITER: WriterAgent(),
            AgentType.FACTCHECKER: FactCheckerAgent(),
            AgentType.VALIDATOR: ValidatorAgent(),
            AgentType.SEO: SEOAgent(),
            AgentType.PUBLISHER: PublisherAgent(),
            AgentType.SOCIAL: SocialAgent(),
            AgentType.ANALYTICS: AnalyticsAgent(),
            AgentType.EVERGREEN: EvergreenAgent(),
        }

    async def dispatch(self, job: JobContract) -> JobContract:
        agent = self.agents.get(job.agent)
        if not agent:
            raise ValueError(f"No registered agent handler for agent type: {job.agent}")
        return await agent.execute_job(job)
