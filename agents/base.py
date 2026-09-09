"""
Abstract BaseAgent defining the standard stateless contract for all EDGE agents.
"""

from abc import ABC, abstractmethod
import time
from typing import Dict, Any, Optional
from packages.schemas import JobContract, JobStatus, AgentType, JobMetadata
from packages.llm import LLMClient


class BaseAgent(ABC):
    agent_type: AgentType

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    async def execute_job(self, job: JobContract) -> JobContract:
        """
        Standard execution lifecycle:
        1. Validate job inputs
        2. Execute agent logic
        3. Measure latency & capture metadata
        4. Return updated JobContract
        """
        start_time = time.time()
        job.status = JobStatus.PROCESSING

        try:
            output_payload = await self.process(job.article_id, job.input_payload)
            job.output_payload = output_payload
            job.status = JobStatus.COMPLETED
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            if job.attempt >= job.max_attempts:
                job.status = JobStatus.DEAD_LETTER

        latency_ms = (time.time() - start_time) * 1000.0
        job.metadata.latency_ms = latency_ms
        return job

    @abstractmethod
    async def process(self, article_id: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Subclasses implement domain-specific agent logic."""
        pass
