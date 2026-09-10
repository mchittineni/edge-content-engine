"""
CLI smoke and behaviour tests using Click's isolated runner.

These assert exit codes and observable output, not formatting details, so the
terminal presentation can evolve without churning the suite.
"""

import pytest
from click.testing import CliRunner

import cli.approval as cli_approval
import cli.main as cli_main
from cli.main import cli
from packages.schemas import ArticleRecord, ArticleStatus
from packages.storage.lake import ContentLake


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def cli_lake(monkeypatch: pytest.MonkeyPatch, isolated_test_env: str) -> ContentLake:
    """
    Point every CLI command at an isolated lake.

    `default_lake` is a module-level singleton bound at import time, so each
    importing module holds its own reference and every one must be patched.
    See docs/adr/0003-content-lake-storage-abstraction.md for the trade-off.
    """
    lake = ContentLake(base_dir=isolated_test_env)
    monkeypatch.setattr(cli_main, "default_lake", lake)
    monkeypatch.setattr(cli_approval, "default_lake", lake)
    return lake


class TestCliSurface:
    def test_help_lists_all_commands(self, runner: CliRunner) -> None:
        res = runner.invoke(cli, ["--help"])
        assert res.exit_code == 0
        for command in ["discover", "pipeline", "review", "publish", "diff-inspect", "list"]:
            assert command in res.output

    @pytest.mark.parametrize(
        "command", ["discover", "pipeline", "review", "publish", "diff-inspect", "list"]
    )
    def test_each_command_has_help(self, runner: CliRunner, command: str) -> None:
        res = runner.invoke(cli, [command, "--help"])
        assert res.exit_code == 0

    def test_unknown_command_fails(self, runner: CliRunner) -> None:
        res = runner.invoke(cli, ["definitely-not-a-command"])
        assert res.exit_code != 0


class TestDiscover:
    def test_discover_lists_opportunities(self, runner: CliRunner, cli_lake: ContentLake) -> None:
        res = runner.invoke(cli, ["discover", "--repo", "mchittineni/IaCSecBench"])
        assert res.exit_code == 0, res.output
        assert "IaCSecBench" in res.output


class TestPipeline:
    def test_pipeline_run_completes(self, runner: CliRunner, cli_lake: ContentLake) -> None:
        res = runner.invoke(
            cli, ["pipeline", "run", "EDGE-CLI-001", "--topic", "Testing pipelines"]
        )
        assert res.exit_code == 0, res.output

    def test_pipeline_rejects_invalid_action(self, runner: CliRunner) -> None:
        res = runner.invoke(cli, ["pipeline", "destroy"])
        assert res.exit_code != 0


class TestListAndReview:
    def test_list_with_no_articles(self, runner: CliRunner, cli_lake: ContentLake) -> None:
        res = runner.invoke(cli, ["list"])
        assert res.exit_code == 0, res.output

    def test_list_shows_saved_article(
        self, runner: CliRunner, cli_lake: ContentLake, sample_article_record: ArticleRecord
    ) -> None:
        cli_lake.save_article_state(sample_article_record)
        res = runner.invoke(cli, ["list"])
        assert res.exit_code == 0, res.output
        assert "EDGE-TEST-001" in res.output

    def test_review_missing_article_is_graceful(
        self, runner: CliRunner, cli_lake: ContentLake
    ) -> None:
        res = runner.invoke(cli, ["review", "NOPE-404"])
        assert res.exit_code == 0, res.output

    def test_review_approves_via_prompt(
        self, runner: CliRunner, cli_lake: ContentLake, sample_article_record: ArticleRecord
    ) -> None:
        sample_article_record.status = ArticleStatus.AWAITING_APPROVAL
        cli_lake.save_article_state(sample_article_record)
        res = runner.invoke(cli, ["review", "EDGE-TEST-001"], input="1\n")
        assert res.exit_code == 0, res.output
        assert cli_lake.load_article_state("EDGE-TEST-001").status == ArticleStatus.APPROVED

    def test_review_rejects_via_prompt(
        self, runner: CliRunner, cli_lake: ContentLake, sample_article_record: ArticleRecord
    ) -> None:
        sample_article_record.status = ArticleStatus.AWAITING_APPROVAL
        cli_lake.save_article_state(sample_article_record)
        res = runner.invoke(cli, ["review", "EDGE-TEST-001"], input="3\n")
        assert res.exit_code == 0, res.output
        assert cli_lake.load_article_state("EDGE-TEST-001").status == ArticleStatus.REJECTED


class TestPublish:
    def test_publish_missing_article_is_graceful(
        self, runner: CliRunner, cli_lake: ContentLake
    ) -> None:
        res = runner.invoke(cli, ["publish", "NOPE-404"])
        assert res.exit_code == 0, res.output


class TestDiffInspect:
    def test_diff_inspect_large_diff_is_interesting(self, runner: CliRunner) -> None:
        res = runner.invoke(cli, ["diff-inspect", "12"])
        assert res.exit_code == 0, res.output

    def test_diff_inspect_small_diff(self, runner: CliRunner) -> None:
        res = runner.invoke(cli, ["diff-inspect", "1"])
        assert res.exit_code == 0, res.output
