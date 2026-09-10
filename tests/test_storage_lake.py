"""
Storage lake tests.

The path-traversal cases here are security regression tests guarding the
hardening introduced in commits 63ab3cc / d60c5eb / 3fd48af / 49721f5
(CWE-22 directory traversal, CWE-73 external control of file name).
Do not delete these without replacing the control they cover.
"""

import json
from pathlib import Path

import pytest

from packages.schemas import ArticleRecord, ArticleStatus
from packages.storage.lake import ContentLake

# Payloads that must never be able to escape the lake's subdirectory.
TRAVERSAL_PAYLOADS = [
    "../etc/passwd",
    "../../etc/passwd",
    "....//....//etc/passwd",
    "/etc/passwd",
    "subdir/nested.json",
    "..\\windows\\system32",
    "foo/../../bar.json",
    "with space.json",
    "semi;colon.json",
    "pipe|char.json",
    "null\x00byte.json",
    "$(whoami).json",
    "`id`.json",
]


class TestPathTraversalDefence:
    @pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
    def test_resolve_safe_path_rejects_traversal(
        self, mock_lake: ContentLake, payload: str
    ) -> None:
        with pytest.raises(ValueError, match=r"Invalid or unsafe filename|Path traversal detected"):
            mock_lake._resolve_safe_path("state", payload)

    @pytest.mark.parametrize("payload", TRAVERSAL_PAYLOADS)
    def test_save_raw_rejects_traversal(self, mock_lake: ContentLake, payload: str) -> None:
        with pytest.raises(ValueError, match=r"Invalid or unsafe filename|Path traversal detected"):
            mock_lake.save_raw(payload, "malicious content")

    def test_resolved_path_always_stays_inside_base_dir(self, mock_lake: ContentLake) -> None:
        resolved = mock_lake._resolve_safe_path("state", "EDGE-2026-001.json")
        assert resolved.resolve().is_relative_to(mock_lake.base_dir.resolve())

    def test_accepts_legitimate_filenames(self, mock_lake: ContentLake) -> None:
        for name in ["EDGE-2026-001.json", "article_v2.md", "a.b.c.txt"]:
            assert mock_lake._resolve_safe_path("drafts", name).name == name

    def test_traversal_does_not_write_outside_lake(self, mock_lake: ContentLake, tmp_path) -> None:
        """A rejected write must leave no file anywhere on disk."""
        canary = tmp_path / "canary.txt"
        with pytest.raises(ValueError, match=r"Invalid or unsafe filename"):
            mock_lake.save_raw(f"../../{canary}", "pwned")
        assert not canary.exists()


class TestLakeRoundTrip:
    def test_save_and_load_article_state(
        self, mock_lake: ContentLake, sample_article_record: ArticleRecord
    ) -> None:
        path = Path(mock_lake.save_article_state(sample_article_record))
        assert path.exists()
        loaded = mock_lake.load_article_state(sample_article_record.id)
        assert loaded is not None
        assert loaded.id == sample_article_record.id
        assert loaded.topic == sample_article_record.topic

    def test_load_missing_article_returns_none(self, mock_lake: ContentLake) -> None:
        assert mock_lake.load_article_state("DOES-NOT-EXIST") is None

    def test_save_raw_research_draft_and_diagram(self, mock_lake: ContentLake) -> None:
        assert Path(mock_lake.save_raw("src1", '{"a": 1}')).exists()
        assert Path(mock_lake.save_research("EDGE-1", {"claims": []})).exists()
        assert Path(mock_lake.save_draft("EDGE-1", 2, "# Draft")).exists()
        assert Path(mock_lake.save_diagram("EDGE-1", "topology.txt", "[a]->[b]")).exists()

    def test_list_articles_sorted_newest_first(self, mock_lake: ContentLake) -> None:
        for idx in range(3):
            mock_lake.save_article_state(
                ArticleRecord(
                    id=f"EDGE-{idx}",
                    topic=f"Topic {idx}",
                    category="architecture",
                    status=ArticleStatus.DISCOVERED,
                )
            )
        articles = mock_lake.list_articles()
        assert len(articles) == 3
        assert articles == sorted(articles, key=lambda a: a.created_at, reverse=True)

    def test_corrupt_state_file_is_skipped_not_fatal(
        self, mock_lake: ContentLake, sample_article_record: ArticleRecord
    ) -> None:
        mock_lake.save_article_state(sample_article_record)
        (mock_lake.base_dir / "state" / "corrupt.json").write_text("{not json", encoding="utf-8")
        articles = mock_lake.list_articles()
        assert [a.id for a in articles] == [sample_article_record.id]

    def test_corrupt_target_state_file_loads_as_none(self, mock_lake: ContentLake) -> None:
        (mock_lake.base_dir / "state" / "BROKEN.json").write_text("{not json", encoding="utf-8")
        assert mock_lake.load_article_state("BROKEN") is None

    def test_schema_violating_state_file_loads_as_none(self, mock_lake: ContentLake) -> None:
        (mock_lake.base_dir / "state" / "WRONG.json").write_text(
            json.dumps({"unexpected": "shape"}), encoding="utf-8"
        )
        assert mock_lake.load_article_state("WRONG") is None


class TestLakeConfiguration:
    def test_creates_all_subdirectories(self, mock_lake: ContentLake) -> None:
        for subdir in ["raw", "research", "drafts", "diagrams", "published", "analytics", "state"]:
            assert (mock_lake.base_dir / subdir).is_dir()

    def test_s3_disabled_outside_prod(self, mock_lake: ContentLake) -> None:
        assert mock_lake.is_s3 is False

    def test_s3_enabled_in_prod_with_bucket(
        self, monkeypatch: pytest.MonkeyPatch, isolated_test_env: str
    ) -> None:
        monkeypatch.setenv("EDGE_ENV", "prod")
        lake = ContentLake(base_dir=isolated_test_env, s3_bucket="edge-prod")
        assert lake.is_s3 is True
