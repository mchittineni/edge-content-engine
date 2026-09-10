"""
Contract tests for the FastAPI review/webhook surface.

Covers happy paths, error paths, and the path-parameter validation that keeps
untrusted article ids away from the storage lake.
"""

import pytest
from fastapi.testclient import TestClient

import apps.api.main as api_main
from apps.api.main import app
from packages.schemas import ArticleRecord, ArticleStatus
from packages.storage.lake import ContentLake


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, isolated_test_env: str) -> TestClient:
    """TestClient bound to an isolated lake instead of the module-level singleton."""
    lake = ContentLake(base_dir=isolated_test_env)
    monkeypatch.setattr(api_main, "default_lake", lake)
    return TestClient(app)


@pytest.fixture
def seeded_client(client: TestClient, sample_article_record: ArticleRecord) -> TestClient:
    api_main.default_lake.save_article_state(sample_article_record)
    return client


class TestHealth:
    def test_healthz_returns_ok(self, client: TestClient) -> None:
        res = client.get("/healthz")
        assert res.status_code == 200
        assert res.json() == {"status": "ok", "service": "edge-content-engine"}


class TestArticleQueries:
    def test_list_articles_empty(self, client: TestClient) -> None:
        res = client.get("/api/v1/articles")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_articles_returns_seeded(self, seeded_client: TestClient) -> None:
        res = seeded_client.get("/api/v1/articles")
        assert res.status_code == 200
        assert [a["id"] for a in res.json()] == ["EDGE-TEST-001"]

    def test_get_article_found(self, seeded_client: TestClient) -> None:
        res = seeded_client.get("/api/v1/articles/EDGE-TEST-001")
        assert res.status_code == 200
        assert res.json()["id"] == "EDGE-TEST-001"

    def test_get_article_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/articles/NOPE-404")
        assert res.status_code == 404
        assert res.json()["detail"] == "Article not found"

    @pytest.mark.parametrize(
        "bad_id",
        ["bad%20id", "bad.id", "id%3Bwhoami", "%2e%2e%2f%2e%2e%2fetc%2fpasswd", "id%00null"],
    )
    def test_get_article_rejects_malformed_ids(self, client: TestClient, bad_id: str) -> None:
        """The route pattern must reject anything outside [A-Za-z0-9_-]."""
        res = client.get(f"/api/v1/articles/{bad_id}")
        assert res.status_code in (404, 422), res.status_code


class TestReviewActions:
    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            ("approve", ArticleStatus.APPROVED),
            ("request_changes", ArticleStatus.CHANGES_REQUESTED),
            ("reject", ArticleStatus.REJECTED),
        ],
    )
    def test_review_transitions_state(
        self, seeded_client: TestClient, action: str, expected: ArticleStatus
    ) -> None:
        res = seeded_client.post("/api/v1/articles/EDGE-TEST-001/review", json={"action": action})
        assert res.status_code == 200
        assert res.json()["new_state"] == expected.value
        assert api_main.default_lake.load_article_state("EDGE-TEST-001").status == expected

    def test_request_changes_increments_revisions(self, seeded_client: TestClient) -> None:
        seeded_client.post(
            "/api/v1/articles/EDGE-TEST-001/review",
            json={"action": "request_changes", "feedback": "tighten the intro"},
        )
        assert api_main.default_lake.load_article_state("EDGE-TEST-001").revisions_count == 1

    def test_review_invalid_action_returns_400(self, seeded_client: TestClient) -> None:
        res = seeded_client.post(
            "/api/v1/articles/EDGE-TEST-001/review", json={"action": "launch_missiles"}
        )
        assert res.status_code == 400
        assert res.json()["detail"] == "Invalid action"

    def test_review_unknown_article_returns_404(self, client: TestClient) -> None:
        res = client.post("/api/v1/articles/NOPE/review", json={"action": "approve"})
        assert res.status_code == 404

    def test_review_missing_action_returns_422(self, seeded_client: TestClient) -> None:
        res = seeded_client.post("/api/v1/articles/EDGE-TEST-001/review", json={})
        assert res.status_code == 422


class TestGitHubWebhook:
    def test_webhook_flags_interesting_event(self, client: TestClient) -> None:
        payload = {
            "action": "push",
            "repository": {"full_name": "mchittineni/IaCSecBench"},
            "commits": [
                {
                    "added": ["benchmarks/opa_latency_eval.py", "infra/main.tf"],
                    "modified": [f"src/mod_{i}.py" for i in range(6)],
                }
            ],
        }
        res = client.post("/api/v1/webhooks/github", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["received"] is True
        assert body["is_interesting"] is True

    def test_webhook_ignores_trivial_event(self, client: TestClient) -> None:
        payload = {
            "action": "push",
            "repository": {"full_name": "mchittineni/notes"},
            "commits": [{"added": [], "modified": ["README.md"]}],
        }
        res = client.post("/api/v1/webhooks/github", json=payload)
        assert res.status_code == 200
        assert res.json()["is_interesting"] is False

    def test_webhook_handles_empty_payload(self, client: TestClient) -> None:
        res = client.post("/api/v1/webhooks/github", json={})
        assert res.status_code == 200
        assert res.json()["received"] is True
