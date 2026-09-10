"""Cost auditor output tests."""

import re

from packages.observability.cost import ArticleCostAuditor

# Rich splits styled runs with ANSI escapes, so "EDGE-TEST-001" can arrive as
# "EDGE-TEST-<esc>001". Assert on de-styled text so these tests do not depend
# on whether colour is enabled (CI vs local, TTY vs pipe).
_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


class TestArticleCostAuditor:
    def test_prints_each_record_and_total(self, capsys) -> None:
        ArticleCostAuditor.print_breakdown(
            "EDGE-TEST-001",
            [
                {"agent": "writer", "cost_usd": 0.1234, "model": "gemini-flash"},
                {"agent": "seo", "cost_usd": 0.0500, "model": "gemini-flash"},
            ],
        )
        out = _plain(capsys.readouterr().out)
        assert "EDGE-TEST-001" in out
        assert "writer" in out
        assert "seo" in out
        assert "0.1734" in out  # total

    def test_handles_empty_records(self, capsys) -> None:
        ArticleCostAuditor.print_breakdown("EDGE-EMPTY", [])
        out = _plain(capsys.readouterr().out)
        assert "EDGE-EMPTY" in out
        assert "0.0000" in out

    def test_tolerates_missing_fields(self, capsys) -> None:
        ArticleCostAuditor.print_breakdown("EDGE-PARTIAL", [{}])
        assert "Unknown" in _plain(capsys.readouterr().out)
