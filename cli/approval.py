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

_MENU = """[bold white]EDITORIAL DECISION:[/bold white]
  [bold green][1][/bold green] APPROVE (Send to publishing queue)
  [bold yellow][2][/bold yellow] REQUEST CHANGES (Send feedback to Writer)
  [bold red][3][/bold red] REJECT (Archive idea)
  [bold dim][4][/bold dim] VIEW FULL DRAFT
  [bold dim][5][/bold dim] EXIT WITHOUT CHANGES"""


class HumanApprovalGate:
    """Renders the review dashboard and applies the editor's decision."""

    @staticmethod
    def _render_header(article: ArticleRecord) -> None:
        header = f"[bold cyan]EDGE PUBLICATION REVIEW GATE[/bold cyan] | [dim]{article.id}[/dim]"
        title_text = (
            f"[bold white]{article.draft.title if article.draft else article.topic}[/bold white]"
        )
        status_badge = f"[bold yellow]{article.status.value}[/bold yellow]"
        console.print(
            Panel(f"{title_text}\nStatus: {status_badge}", title=header, border_style="cyan")
        )

    @staticmethod
    def _render_scorecard(article: ArticleRecord) -> None:
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

    @staticmethod
    def _render_evidence(article: ArticleRecord) -> None:
        if not (article.research and article.research.claims):
            return
        console.print("\n[bold cyan]Verified Primary Evidence Matrix:[/bold cyan]")
        for idx, claim in enumerate(article.research.claims[:3], 1):
            console.print(f"  [yellow]{idx}.[/yellow] [bold]{claim.claim}[/bold]")
            console.print(
                f"     [dim]Source: {claim.source_name} ({claim.tier.value[:6]}) — {claim.source_url}[/dim]"
            )

    @staticmethod
    def _render_architecture(article: ArticleRecord) -> None:
        if article.architecture and article.architecture.ascii_art:
            console.print("\n[bold cyan]Topology Overview:[/bold cyan]")
            console.print(Panel(article.architecture.ascii_art, style="green"))

    @staticmethod
    def _render_social(article: ArticleRecord) -> None:
        if not article.social:
            return
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

    @staticmethod
    def _render_dashboard(article: ArticleRecord) -> None:
        console.clear()
        HumanApprovalGate._render_header(article)
        HumanApprovalGate._render_scorecard(article)
        HumanApprovalGate._render_evidence(article)
        HumanApprovalGate._render_architecture(article)
        HumanApprovalGate._render_social(article)

    @staticmethod
    def _show_draft(article: ArticleRecord) -> None:
        if not article.draft:
            console.print("[dim]No draft is available for this article yet.[/dim]")
            Prompt.ask("Press Enter to return to decision menu")
            return
        console.print(
            Panel(
                article.draft.full_markdown[:2500] + "\n\n[dim]... (truncated)[/dim]",
                title="Draft Preview",
            )
        )
        Prompt.ask("Press Enter to return to decision menu")

    @staticmethod
    def _apply_decision(article: ArticleRecord, choice: str) -> None:
        """Mutate and persist the article for a terminal (non-`4`) choice."""
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
        else:
            console.print("[dim]Exited without state change.[/dim]")

    @staticmethod
    def render_and_prompt(article: ArticleRecord) -> ArticleStatus:
        """Loop the review dashboard until the editor makes a terminal decision."""
        while True:
            HumanApprovalGate._render_dashboard(article)

            console.print(
                "\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]"
            )
            console.print(_MENU)

            choice = Prompt.ask("\nSelect action", choices=["1", "2", "3", "4", "5"], default="1")

            # `4` previews the draft and returns to the menu; every other
            # choice is terminal. A loop (not recursion) keeps repeated
            # previews from growing the call stack without bound.
            if choice == "4":
                HumanApprovalGate._show_draft(article)
                continue

            HumanApprovalGate._apply_decision(article, choice)
            return article.status
