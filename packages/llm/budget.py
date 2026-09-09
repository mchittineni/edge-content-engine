"""
Cost tracker and budget enforcer per article.
"""

from typing import Any, Dict

from packages.llm.routing import MODEL_PRICING_PER_1M_TOKENS


class BudgetExceededError(Exception):
    pass


class ArticleBudgetTracker:
    def __init__(self, max_cost_usd: float = 2.50):
        self.max_cost_usd = max_cost_usd
        self.current_cost_usd = 0.0
        self.history: list[Dict[str, Any]] = []

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        agent_name: str,
    ) -> float:
        pricing = MODEL_PRICING_PER_1M_TOKENS.get(model, {"input": 0.50, "output": 1.50})
        cost = (input_tokens / 1_000_000 * pricing["input"]) + (
            output_tokens / 1_000_000 * pricing["output"]
        )

        self.current_cost_usd += cost
        self.history.append(
            {
                "agent": agent_name,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
                "cumulative_cost_usd": self.current_cost_usd,
            }
        )

        if self.current_cost_usd > self.max_cost_usd:
            raise BudgetExceededError(
                f"Article exceeded budget limit of ${self.max_cost_usd:.2f} (Current: ${self.current_cost_usd:.2f})"
            )

        return cost
