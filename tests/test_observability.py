"""Cost auditor output tests."""

from packages.observability.cost import ArticleCostAuditor


class TestArticleCostAuditor:
    def test_prints_each_record_and_total(self, capsys) -> None:
        ArticleCostAuditor.print_breakdown(
            "EDGE-TEST-001",
            [
                {"agent": "writer", "cost_usd": 0.1234, "model": "gemini-flash"},
                {"agent": "seo", "cost_usd": 0.0500, "model": "gemini-flash"},
            ],
        )
        out = capsys.readouterr().out
        assert "EDGE-TEST-001" in out
        assert "writer" in out
        assert "seo" in out
        assert "0.1734" in out  # total

    def test_handles_empty_records(self, capsys) -> None:
        ArticleCostAuditor.print_breakdown("EDGE-EMPTY", [])
        out = capsys.readouterr().out
        assert "EDGE-EMPTY" in out
        assert "0.0000" in out

    def test_tolerates_missing_fields(self, capsys) -> None:
        ArticleCostAuditor.print_breakdown("EDGE-PARTIAL", [{}])
        out = capsys.readouterr().out
        assert "Unknown" in out
