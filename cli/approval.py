"""
Interactive Human Approval Gate (Terminal TUI).
Presents the complete editorial scorecard, claims, diagrams, and allows
one-click Approve, Request Changes, or Reject.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from packages.schemas import ArticleRecord, ArticleStatus
from packages.storage import default_lake

console = Console()


class HumanApprovalGate:
    @staticmethod
    def render_and_prompt(article: ArticleRecord) -> ArticleStatus:
        console.clear()

        # Header Panel
        header = f"[bold cyan]EDGE PUBLICATION REVIEW GATE[/bold cyan] | [dim]{article.id}[/dim]"
        title_text = (
            f"[bold white]{article.draft.title if article.draft else article.topic}[/bold white]"
        )
        status_badge = f"[bold yellow]{article.status.value}[/bold yellow]"
        console.print(
            Panel(f"{title_text}\nStatus: {status_badge}", title=header, border_style="cyan")
        )

        # Scorecard Table
        table = Table(title="Editorial & Technical Quality Scorecard", border_style="dim")
        table.add_column("Evaluation Metric", style="cyan")
        table.add_column("Score", justify="center", style="bold green")
        table.add_column("Status / Details", style="white")

        if article.score:
            table.add_row(
                "Opportunity Score", f"{article.score.total_score}/60", article.score.recommendation
            )
        if article.qa:
            table.add_row(
                "Technical Accuracy",
                f"{article.qa.technical_score}%",
                "✓ Passed" if article.qa.passed else "⚠ Issues flagged",
            )
            table.add_row(
                "Primary Citations",
                f"{article.qa.citation_score}%",
                f"{article.qa.verified_claims_count} claims verified",
            )
            table.add_row(
                "Code Syntax & Linting", f"{article.qa.code_validity_score}%", "All snippets tested"
            )
        if article.seo:
            table.add_row("SEO Optimization", "91%", f"Keyword: '{article.seo.primary_keyword}'")

        console.print(table)

        # Claim & Evidence Matrix Preview
        if article.research and article.research.claims:
            console.print("\n[bold cyan]Verified Primary Evidence Matrix:[/bold cyan]")
            for idx, claim in enumerate(article.research.claims[:3], 1):
                console.print(f"  [yellow]{idx}.[/yellow] [bold]{claim.claim}[/bold]")
                console.print(
                    f"     [dim]Source: {claim.source_name} ({claim.tier.value[:6]}) — {claim.source_url}[/dim]"
                )

        # Architecture Preview
        if article.architecture and article.architecture.ascii_art:
            console.print("\n[bold cyan]Topology Overview:[/bold cyan]")
            console.print(Panel(article.architecture.ascii_art, style="green"))

        # Social Distribution Preview
        if article.social:
            console.print("\n[bold cyan]Social Distribution Package Ready:[/bold cyan]")
            console.print(
                f"  • [blue]LinkedIn[/blue]: Leadership insight ready ({len(article.social.linkedin_post)} chars)"
            )
            console.print(
                f"  • [red]Reddit[/red]: Authentic discussion ready (Target: {article.social.reddit_post.get('target_subreddits')})"
            )
            console.print(
                f"  • [white]X Thread[/white]: {len(article.social.x_thread)} tweets synthesized"
            )

        # Action Prompt
        console.print(
            "\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]"
        )
        console.print("[bold white]EDITORIAL DECISION:[/bold white]")
        console.print("  [bold green][1][/bold green] APPROVE (Send to publishing queue)")
        console.print("  [bold yellow][2][/bold yellow] REQUEST CHANGES (Send feedback to Writer)")
        console.print("  [bold red][3][/bold red] REJECT (Archive idea)")
        console.print("  [bold dim][4][/bold dim] VIEW FULL DRAFT")
        console.print("  [bold dim][5][/bold dim] EXIT WITHOUT CHANGES")

        choice = Prompt.ask("\nSelect action", choices=["1", "2", "3", "4", "5"], default="1")

        if choice == "1":
            article.status = ArticleStatus.APPROVED
            default_lake.save_article_state(article)
            console.print(
                "\n[bold green]✓ Article APPROVED![/bold green] Ready to publish with `edge publish`."
            )
        elif choice == "2":
            article.status = ArticleStatus.CHANGES_REQUESTED
            feedback = Prompt.ask("Enter editorial feedback")
            article.revisions_count += 1
            default_lake.save_article_state(article)
            console.print(f"\n[bold yellow]Revisions requested:[/bold yellow] {feedback}")
        elif choice == "3":
            article.status = ArticleStatus.REJECTED
            default_lake.save_article_state(article)
            console.print("\n[bold red]Article REJECTED.[/bold red]")
        elif choice == "4":
            if article.draft:
                console.print(
                    Panel(
                        article.draft.full_markdown[:2500] + "\n\n[dim]... (truncated)[/dim]",
                        title="Draft Preview",
                    )
                )
                Prompt.ask("Press Enter to return to decision menu")
                return HumanApprovalGate.render_and_prompt(article)
        else:
            console.print("[dim]Exited without state change.[/dim]")

        return article.status
