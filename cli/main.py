"""
EDGE Content Engine CLI: Main entrypoint for discovery, pipeline runs,
human review, and publishing.
"""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from apps.workers.dispatcher import AgentDispatcher
from apps.workers.pipeline import ArticlePipelineOrchestrator
from cli.approval import HumanApprovalGate
from packages.beehiiv import BeehiivClient
from packages.github import GitHubEventNormalizer
from packages.schemas import AgentType, ArticleStatus, JobContract
from packages.storage import default_lake

console = Console()


@click.group()
def cli() -> None:
    """EDGE Content Engine: Autonomous Multi-Agent Engineering-Media Pipeline."""


@cli.command("discover")
@click.option("--repo", default="mchittineni/tf-arch-diagram-generator", help="GitHub repo to scan")
def discover(repo: str) -> None:
    """Scan GitHub and ecosystems to discover candidate articles."""
    console.print(f"[bold cyan]Scanning sources & GitHub repository:[/bold cyan] {repo}...")
    dispatcher = AgentDispatcher()
    job = JobContract(
        article_id="EDGE-DISCOVER",
        agent=AgentType.DISCOVERY,
        input_payload={"source_type": "github", "repo_name": repo},
    )
    result = asyncio.run(dispatcher.dispatch(job))
    opportunities = result.output_payload.get("opportunities", [])

    table = Table(title="Discovered Candidate Opportunities", border_style="cyan")
    table.add_column("#", style="dim")
    table.add_column("Proposed Topic", style="bold white")
    table.add_column("Category", style="yellow")
    table.add_column("Source Context", style="dim")

    for idx, opp in enumerate(opportunities, 1):
        table.add_row(str(idx), opp["topic"], opp["category"], opp["source"])

    console.print(table)
    console.print(
        '[dim]Run `edge pipeline run <id> --topic "..."` to trigger editorial synthesis.[/dim]'
    )


@cli.command("pipeline")
@click.argument("action", type=click.Choice(["run"]))
@click.argument("article_id", default="EDGE-2026-001")
@click.option(
    "--topic", default="Terraform plans are terrible architecture diagrams", help="Article topic"
)
@click.option("--category", default="architecture", help="Article category")
def run_pipeline_cmd(action: str, article_id: str, topic: str, category: str) -> None:
    """Execute the full editorial pipeline up to the approval gate."""
    orchestrator = ArticlePipelineOrchestrator()
    asyncio.run(orchestrator.run_pipeline(article_id=article_id, topic=topic, category=category))


@cli.command("review")
@click.argument("article_id", default="EDGE-2026-001")
def review(article_id: str) -> None:
    """Open the interactive terminal review & approval gate."""
    article = default_lake.load_article_state(article_id)
    if not article:
        console.print(
            f"[bold red]Article {article_id} not found.[/bold red] Run `edge pipeline run {article_id}` first."
        )
        return
    HumanApprovalGate.render_and_prompt(article)


@cli.command("publish")
@click.argument("article_id", default="EDGE-2026-001")
def publish(article_id: str) -> None:
    """Publish an approved article to Beehiiv and display social distribution packages."""
    article = default_lake.load_article_state(article_id)
    if not article:
        console.print(f"[bold red]Article {article_id} not found.[/bold red]")
        return
    if article.status != ArticleStatus.APPROVED:
        console.print(
            f"[bold yellow]Cannot publish article with status: {article.status.value}.[/bold yellow] Must be APPROVED first."
        )
        return
    if not article.draft:
        console.print(f"[bold red]Article {article_id} has no draft.[/bold red]")
        return

    console.print(f"[bold cyan]Publishing {article.id} downstream to Beehiiv API...[/bold cyan]")
    beehiiv = BeehiivClient()
    record = asyncio.run(beehiiv.create_draft_post(article.draft))
    article.publication = record
    article.status = ArticleStatus.PUBLISHED
    default_lake.save_article_state(article)

    console.print("[bold green]✓ Successfully published to Beehiiv![/bold green]")
    console.print(f"  Post ID: [yellow]{record.post_id}[/yellow]")
    if record.web_url:
        console.print(f"  Live Preview URL: [cyan]{record.web_url}[/cyan]\n")

    if article.social:
        console.print(
            "[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]"
        )
        console.print("[bold white]READY FOR MULTI-PLATFORM DISTRIBUTION:[/bold white]")
        console.print(
            "[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]\n"
        )
        console.print("[bold cyan][LinkedIn Post][/bold cyan]")
        console.print(article.social.linkedin_post)
        console.print("\n[bold cyan][Reddit Discussion Post (Anti-Spam / Organic)][/bold cyan]")
        console.print(f"[bold]Title:[/bold] {article.social.reddit_post.get('title')}")
        console.print(f"[bold]Body:[/bold] {article.social.reddit_post.get('body')}")
        console.print(f"[bold]Prompt:[/bold] {article.social.reddit_post.get('discussion_prompt')}")


@cli.command("diff-inspect")
@click.argument("files_changed", type=int, default=12)
@click.option("--benchmark", is_flag=True, default=True, help="Simulate benchmark modification")
def diff_inspect(files_changed: int, benchmark: bool) -> None:
    """Inspect a simulated or real git diff to see if it triggers an editorial idea."""
    normalizer = GitHubEventNormalizer()
    payload = {
        "repository": {"full_name": "mchittineni/IaCSecBench"},
        "commits": [
            {
                "added": ["benchmarks/opa_latency_eval.py", "benchmarks/policy_results.json"],
                "modified": ["README.md", "evals/security_tests.py"]
                + [f"tests/test_{i}.py" for i in range(files_changed)],
                "removed": [],
            }
        ],
        "ref": "refs/heads/main",
    }
    event = normalizer.normalize("push", payload)
    console.print(
        f"[bold]Is Editorially Interesting:[/bold] {'[green]YES[/green]' if event.is_interesting else '[red]NO[/red]'}"
    )
    console.print(f"[bold]Event Headline:[/bold] {event.headline}")
    console.print(f"[bold]Editorial Rationale:[/bold] {event.rationale}")


@cli.command("list")
def list_articles() -> None:
    """List all tracked articles and their lifecycle status."""
    articles = default_lake.list_articles()
    table = Table(title="EDGE Content Pipeline State", border_style="cyan")
    table.add_column("ID", style="bold cyan")
    table.add_column("Status", style="bold yellow")
    table.add_column("Topic", style="white")
    table.add_column("Revisions", justify="center")

    for art in articles:
        table.add_row(
            art.id,
            art.status.value,
            art.topic[:55] + ("..." if len(art.topic) > 55 else ""),
            str(art.revisions_count),
        )

    console.print(table)


if __name__ == "__main__":
    cli()
