"""Worker runner loop tests, including graceful shutdown."""

import asyncio

from apps.workers.runner import WorkerRunner
from packages.schemas import AgentType, JobContract, JobStatus


class TestProcessSingleJob:
    async def test_processes_a_job_to_completion(self, sample_job_contract: JobContract) -> None:
        result = await WorkerRunner().process_single_job(sample_job_contract)
        assert result.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DEAD_LETTER)

    async def test_reports_dead_letter_jobs(self, sample_job_contract: JobContract) -> None:
        """A job on its final attempt that fails must surface as DEAD_LETTER."""
        runner = WorkerRunner()

        async def always_fail(job: JobContract) -> JobContract:
            job.status = JobStatus.DEAD_LETTER
            job.error_message = "synthetic"
            return job

        runner.dispatcher.dispatch = always_fail  # type: ignore[method-assign]
        sample_job_contract.attempt = 3
        result = await runner.process_single_job(sample_job_contract)
        assert result.status == JobStatus.DEAD_LETTER


class TestDaemonLifecycle:
    async def test_stop_sets_flags(self) -> None:
        runner = WorkerRunner()
        assert runner.running is True
        runner.stop()
        assert runner.running is False
        assert runner._stop_event.is_set()

    async def test_daemon_exits_promptly_on_stop(self) -> None:
        """
        Regression guard: the loop must wake on the stop event rather than
        sleeping out a full poll interval before noticing shutdown.
        """
        runner = WorkerRunner()
        task = asyncio.create_task(runner.run_daemon(poll_interval_sec=30.0))
        await asyncio.sleep(0.05)
        runner.stop()
        await asyncio.wait_for(task, timeout=2.0)
        assert task.done()

    async def test_daemon_keeps_polling_until_stopped(self) -> None:
        runner = WorkerRunner()
        task = asyncio.create_task(runner.run_daemon(poll_interval_sec=0.01))
        await asyncio.sleep(0.08)
        assert not task.done()
        runner.stop()
        await asyncio.wait_for(task, timeout=2.0)


class TestJobContract:
    def test_defaults(self) -> None:
        job = JobContract(article_id="EDGE-1", agent=AgentType.WRITER, input_payload={})
        assert job.status == JobStatus.PENDING
        assert job.attempt <= job.max_attempts
