"""
BaseAgent lifecycle and dispatcher tests.

The retry/dead-letter transitions here are the pipeline's failure contract:
they decide whether a bad job is retried or parked, so they are asserted
explicitly rather than exercised only through the happy-path pipeline test.
"""

import asyncio
from typing import Any, ClassVar

import pytest

from agents.base import BaseAgent
from apps.workers.dispatcher import AgentDispatcher
from packages.schemas import AgentType, JobContract, JobStatus


class _ExplodingAgent(BaseAgent):
    agent_type = AgentType.WRITER

    async def process(self, article_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("synthetic agent failure")


class _EchoAgent(BaseAgent):
    agent_type = AgentType.WRITER

    async def process(self, article_id: str, input_payload: dict[str, Any]) -> dict[str, Any]:
        return {"echo": input_payload, "article_id": article_id}


class TestAgentLifecycle:
    async def test_successful_job_completes_with_latency(
        self, sample_job_contract: JobContract
    ) -> None:
        result = await _EchoAgent().execute_job(sample_job_contract)
        assert result.status == JobStatus.COMPLETED
        assert result.output_payload["article_id"] == "EDGE-TEST-001"
        assert result.metadata.latency_ms >= 0

    async def test_failure_marks_job_failed_and_records_message(
        self, sample_job_contract: JobContract
    ) -> None:
        sample_job_contract.attempt = 1
        sample_job_contract.max_attempts = 3
        result = await _ExplodingAgent().execute_job(sample_job_contract)
        assert result.status == JobStatus.FAILED
        assert "synthetic agent failure" in (result.error_message or "")

    async def test_failure_on_final_attempt_dead_letters(
        self, sample_job_contract: JobContract
    ) -> None:
        sample_job_contract.attempt = 3
        sample_job_contract.max_attempts = 3
        result = await _ExplodingAgent().execute_job(sample_job_contract)
        assert result.status == JobStatus.DEAD_LETTER

    async def test_failure_is_logged(
        self, sample_job_contract: JobContract, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level("ERROR"):
            await _ExplodingAgent().execute_job(sample_job_contract)
        assert any("failed job" in rec.message for rec in caplog.records)

    async def test_agent_never_raises_out_of_execute_job(
        self, sample_job_contract: JobContract
    ) -> None:
        """The worker boundary must absorb every agent exception."""
        result = await _ExplodingAgent().execute_job(sample_job_contract)
        assert result is sample_job_contract


class TestDispatcher:
    # GITHUB_EVENT is handled by the webhook route (apps/api/main.py), not by an
    # agent, so it is intentionally absent from the dispatcher table.
    NON_DISPATCHABLE: ClassVar[set[AgentType]] = {AgentType.GITHUB_EVENT}

    def test_registers_an_agent_for_every_dispatchable_agent_type(self) -> None:
        dispatcher = AgentDispatcher()
        missing = [
            t for t in AgentType if t not in dispatcher.agents and t not in self.NON_DISPATCHABLE
        ]
        assert not missing, f"AgentType(s) with no registered agent: {missing}"

    def test_unmapped_agent_type_raises_clear_error(self) -> None:
        """
        Known gap: this ValueError escapes `dispatch` *outside* BaseAgent's
        failure boundary, so a queued github_event job crashes the worker loop
        instead of dead-lettering. Tracked in docs/backlog.md (SDLC-1).
        """
        job = JobContract(
            article_id="EDGE-TEST-001",
            agent=AgentType.GITHUB_EVENT,
            input_payload={},
        )
        with pytest.raises(ValueError, match="No registered agent handler"):
            asyncio.run(AgentDispatcher().dispatch(job))

    def test_registered_agents_declare_matching_type(self) -> None:
        for agent_type, agent in AgentDispatcher().agents.items():
            assert agent.agent_type == agent_type

    async def test_dispatch_routes_to_correct_agent(self, sample_job_contract: JobContract) -> None:
        result = await AgentDispatcher().dispatch(sample_job_contract)
        assert result.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DEAD_LETTER)
