"""
Observability, tracing, and structured cost accounting.
"""

from typing import Any

from rich.console import Console

console = Console()


class ArticleCostAuditor:
    @staticmethod
    def print_breakdown(article_id: str, cost_records: list[dict[str, Any]]) -> None:
        console.print(
            "\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]"
        )
        console.print(f"[bold white]COST AUDIT & TRACE: {article_id}[/bold white]")
        console.print(
            "[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]"
        )

        total_cost = 0.0
        for item in cost_records:
            agent = item.get("agent", "Unknown")
            cost = item.get("cost_usd", 0.0)
            model = item.get("model", "")
            total_cost += cost
            console.print(
                f"  [cyan]{agent:<22}[/cyan] : [green]${cost:>6.4f}[/green] [dim]({model})[/dim]"
            )

        console.print(
            "[bold cyan]────────────────────────────────────────────────────────────[/bold cyan]"
        )
        console.print(
            f"  [bold yellow]{'TOTAL ESTIMATED COST':<22}[/bold yellow] : [bold green]${total_cost:>6.4f}[/bold green]\n"
        )
