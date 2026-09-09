from packages.github import GitHubEventNormalizer


def test_normalizer_ignores_trivial_push():
    normalizer = GitHubEventNormalizer()
    payload = {
        "repository": {"full_name": "mchittineni/test-repo"},
        "commits": [{"added": ["file1.txt"], "modified": [], "removed": []}],
        "ref": "refs/heads/main",
    }
    event = normalizer.normalize("push", payload)
    assert not event.is_interesting
    assert "Trivial push ignored" in event.headline


def test_normalizer_ignores_docs_only_push():
    normalizer = GitHubEventNormalizer()
    payload = {
        "repository": {"full_name": "mchittineni/test-repo"},
        "commits": [
            {
                "added": ["README.md", "docs/architecture.md", "images/diagram.png"],
                "modified": ["CHANGELOG.md"],
                "removed": [],
            }
        ],
        "ref": "refs/heads/main",
    }
    event = normalizer.normalize("push", payload)
    assert not event.is_interesting
    assert "Documentation-only push ignored" in event.headline


def test_normalizer_triggers_on_benchmark_and_terraform():
    normalizer = GitHubEventNormalizer()
    payload = {
        "repository": {"full_name": "mchittineni/IaCSecBench"},
        "commits": [
            {
                "added": ["benchmarks/eval_security.py", "modules/vpc/main.tf"],
                "modified": ["tests/test_bench.py", "evals/results.json"],
                "removed": [],
            }
        ],
        "ref": "refs/heads/main",
    }
    event = normalizer.normalize("push", payload)
    assert event.is_interesting
    assert event.category == "benchmark"
