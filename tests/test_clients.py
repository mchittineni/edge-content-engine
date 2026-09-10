"""
HTTP client tests.

Every network call is stubbed with httpx.MockTransport - the suite must never
reach api.github.com or api.beehiiv.com.
"""

import httpx
import pytest

from packages.beehiiv.client import BeehiivClient
from packages.github.client import GitHubAppClient
from packages.schemas import ArticleDraft

# Captured before any monkeypatching so the factory cannot recurse into itself.
_REAL_ASYNC_CLIENT = httpx.AsyncClient


def _mock_client_factory(handler):
    """Build a factory that returns an AsyncClient wired to a mock transport."""

    def factory(*args, **kwargs):
        return _REAL_ASYNC_CLIENT(transport=httpx.MockTransport(handler))

    return factory


class TestGitHubAppClientHeaders:
    def test_omits_authorization_without_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        headers = GitHubAppClient(token=None)._headers()
        assert "Authorization" not in headers
        assert headers["User-Agent"] == "EDGE-Content-Engine/1.0"

    def test_includes_authorization_with_token(self) -> None:
        headers = GitHubAppClient(token="ghp_secret")._headers()
        assert headers["Authorization"] == "token ghp_secret"

    def test_reads_token_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
        assert GitHubAppClient()._headers()["Authorization"] == "token ghp_from_env"


class TestGitHubAppClientCalls:
    async def test_get_repository_details_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/repos/mchittineni/IaCSecBench"
            return httpx.Response(200, json={"full_name": "mchittineni/IaCSecBench", "stars": 12})

        monkeypatch.setattr(httpx, "AsyncClient", _mock_client_factory(handler))
        data = await GitHubAppClient(token="t").get_repository_details("mchittineni", "IaCSecBench")
        assert data["full_name"] == "mchittineni/IaCSecBench"

    async def test_get_repository_details_falls_back_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            httpx, "AsyncClient", _mock_client_factory(lambda r: httpx.Response(404))
        )
        data = await GitHubAppClient(token="t").get_repository_details("owner", "repo")
        assert data == {"name": "repo", "full_name": "owner/repo"}

    async def test_get_latest_commit_returns_empty_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            httpx, "AsyncClient", _mock_client_factory(lambda r: httpx.Response(500))
        )
        assert await GitHubAppClient(token="t").get_latest_commit("o", "r") == {}

    async def test_get_recent_releases_returns_empty_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            httpx, "AsyncClient", _mock_client_factory(lambda r: httpx.Response(403))
        )
        assert await GitHubAppClient(token="t").get_recent_releases("o", "r") == []

    async def test_get_recent_releases_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            httpx,
            "AsyncClient",
            _mock_client_factory(lambda r: httpx.Response(200, json=[{"tag_name": "v1.0.0"}])),
        )
        releases = await GitHubAppClient(token="t").get_recent_releases("o", "r")
        assert releases[0]["tag_name"] == "v1.0.0"


class TestBeehiivClient:
    def test_headers_carry_bearer_token(self) -> None:
        headers = BeehiivClient(api_token="bh_token", publication_id="pub_1")._headers()
        assert headers["Authorization"] == "Bearer bh_token"
        assert headers["Content-Type"] == "application/json"

    async def test_returns_simulated_record_without_credentials(
        self, monkeypatch: pytest.MonkeyPatch, sample_article_draft: ArticleDraft
    ) -> None:
        """Local/dev runs must degrade to a simulated record, never a live call."""
        monkeypatch.delenv("BEEHIIV_API_TOKEN", raising=False)
        monkeypatch.delenv("BEEHIIV_PUBLICATION_ID", raising=False)

        def explode(*args, **kwargs):
            raise AssertionError("no network call may be made without credentials")

        monkeypatch.setattr(httpx, "AsyncClient", explode)

        record = await BeehiivClient(api_token=None, publication_id=None).create_draft_post(
            sample_article_draft
        )
        assert record.post_id == "post_beehiiv_edge_test_001"
