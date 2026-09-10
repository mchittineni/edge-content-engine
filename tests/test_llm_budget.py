"""Budget enforcement and model-routing tests."""

import pytest

from packages.llm.budget import ArticleBudgetTracker, BudgetExceededError
from packages.llm.routing import MODEL_PRICING_PER_1M_TOKENS, TASK_MODEL_MAPPING, TaskTier


class TestBudgetTracker:
    def test_starts_at_zero(self) -> None:
        tracker = ArticleBudgetTracker()
        assert tracker.current_cost_usd == 0.0
        assert tracker.history == []

    def test_records_usage_and_accumulates(self) -> None:
        tracker = ArticleBudgetTracker(max_cost_usd=100.0)
        first = tracker.record_usage("unknown-model", 1_000_000, 1_000_000, "writer")
        assert first == pytest.approx(2.0)  # 0.50 input + 1.50 output default pricing
        tracker.record_usage("unknown-model", 1_000_000, 1_000_000, "seo")
        assert tracker.current_cost_usd == pytest.approx(4.0)
        assert len(tracker.history) == 2

    def test_history_entry_shape(self) -> None:
        tracker = ArticleBudgetTracker(max_cost_usd=100.0)
        tracker.record_usage("unknown-model", 1000, 2000, "researcher")
        entry = tracker.history[0]
        assert entry["agent"] == "researcher"
        assert entry["input_tokens"] == 1000
        assert entry["output_tokens"] == 2000
        assert entry["cumulative_cost_usd"] == pytest.approx(entry["cost_usd"])

    def test_raises_when_budget_exceeded(self) -> None:
        tracker = ArticleBudgetTracker(max_cost_usd=0.01)
        with pytest.raises(BudgetExceededError, match="exceeded budget limit"):
            tracker.record_usage("unknown-model", 10_000_000, 10_000_000, "writer")

    def test_usage_is_recorded_even_when_it_trips_the_limit(self) -> None:
        """The overspending call must still be auditable in history."""
        tracker = ArticleBudgetTracker(max_cost_usd=0.01)
        with pytest.raises(BudgetExceededError):
            tracker.record_usage("unknown-model", 10_000_000, 10_000_000, "writer")
        assert len(tracker.history) == 1
        assert tracker.current_cost_usd > tracker.max_cost_usd

    def test_zero_tokens_cost_nothing(self) -> None:
        tracker = ArticleBudgetTracker()
        assert tracker.record_usage("unknown-model", 0, 0, "scorer") == 0.0

    def test_known_model_uses_its_own_pricing(self) -> None:
        model = next(iter(MODEL_PRICING_PER_1M_TOKENS))
        pricing = MODEL_PRICING_PER_1M_TOKENS[model]
        tracker = ArticleBudgetTracker(max_cost_usd=1000.0)
        cost = tracker.record_usage(model, 1_000_000, 0, "writer")
        assert cost == pytest.approx(pricing["input"])


class TestModelRouting:
    def test_every_task_tier_maps_to_a_model(self) -> None:
        for tier in TaskTier:
            assert TASK_MODEL_MAPPING.get(tier), f"{tier} has no model mapping"

    def test_pricing_entries_have_input_and_output(self) -> None:
        for model, pricing in MODEL_PRICING_PER_1M_TOKENS.items():
            assert "input" in pricing, model
            assert "output" in pricing, model
            assert pricing["input"] >= 0, model
            assert pricing["output"] >= 0, model
