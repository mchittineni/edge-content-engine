"""
Worker Runner Loop: Consumes JobContract messages from local or SQS queues,
executes agents via AgentDispatcher, and records state transitions.
"""

import asyncio

from rich.console import Console

from apps.workers.dispatcher import AgentDispatcher
from packages.schemas import JobContract, JobStatus

console = Console()


class WorkerRunner:
    def __init__(self) -> None:
        self.dispatcher = AgentDispatcher()
        self.running = True
        self._stop_event = asyncio.Event()

    async def process_single_job(self, job: JobContract) -> JobContract:
        console.print(
            f"[bold cyan]Worker[/bold cyan] Processing job [yellow]{job.job_id}[/yellow] for agent [green]{job.agent.value}[/green] (Attempt {job.attempt}/{job.max_attempts})..."
        )

        result_job = await self.dispatcher.dispatch(job)

        if result_job.status == JobStatus.COMPLETED:
            console.print(
                f"[bold green]✓[/bold green] Job [yellow]{job.job_id}[/yellow] ({job.agent.value}) completed successfully in {result_job.metadata.latency_ms:.1f}ms"
            )
        elif result_job.status == JobStatus.DEAD_LETTER:
            console.print(
                f"[bold red]✗ DEAD LETTER:[/bold red] Job [yellow]{job.job_id}[/yellow] failed permanently after {job.max_attempts} attempts: {result_job.error_message}"
            )
        else:
            console.print(
                f"[bold red]✗[/bold red] Job [yellow]{job.job_id}[/yellow] failed: {result_job.error_message}"
            )

        return result_job

    async def run_daemon(self, poll_interval_sec: float = 3.0) -> None:
        console.print(
            "[bold green]EDGE Content Engine Worker Runner started.[/bold green] Listening for queue jobs..."
        )
        while self.running:
            # Poll placeholder for SQS or the local queue file. Waiting on the
            # stop event (rather than sleeping blindly) makes shutdown immediate
            # instead of taking up to one full poll interval.
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=poll_interval_sec)
            except TimeoutError:
                continue

    def stop(self) -> None:
        self.running = False
        self._stop_event.set()


if __name__ == "__main__":
    runner = WorkerRunner()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(runner.run_daemon())
    except KeyboardInterrupt:
        runner.stop()
        console.print("\n[yellow]Worker shutdown gracefully.[/yellow]")
