"""
GitHub Webhook Event Normalizer & Editorial Filter.
Filters out noise and extracts genuine engineering moments into opportunities.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class NormalizedEvent(BaseModel):
    is_interesting: bool
    event_type: str
    repository: str
    ref_or_version: str
    headline: str
    rationale: str
    modified_files: list[str] = []
    category: str = "infrastructure"


class GitHubEventNormalizer:
    """
    Applies strict rule filtering to prevent unnecessary LLM invocation:
    - Ignores trivial changes (< 3 files, doc-only changes)
    - Triggers on benchmarks, Terraform/IaC files, security policies, and major releases
    """

    BENCHMARK_KEYWORDS = ["benchmark", "bench", "iacsecbench", "latency", "throughput", "profile"]
    IAC_KEYWORDS = [".tf", "terraform", "terragrunt", "opentofu", "cloudformation", "k8s", "helm"]
    SECURITY_KEYWORDS = ["opa", "rego", "policy", "cve", "guard", "security", "trivy", "checkov"]

    def normalize(self, event_type: str, payload: Dict[str, Any]) -> NormalizedEvent:
        repo_name = payload.get("repository", {}).get("full_name", "unknown/repo")

        # 1. Release Events
        if event_type == "release":
            action = payload.get("action")
            release = payload.get("release", {})
            tag_name = release.get("tag_name", "")
            is_prerelease = release.get("prerelease", False)

            if action == "published" and not is_prerelease:
                return NormalizedEvent(
                    is_interesting=True,
                    event_type="release",
                    repository=repo_name,
                    ref_or_version=tag_name,
                    headline=f"New Major Release: {repo_name} {tag_name}",
                    rationale=f"Production release published: {release.get('name', tag_name)}",
                    category="release",
                )

        # 2. Push Events
        if event_type == "push":
            commits = payload.get("commits", [])
            ref = payload.get("ref", "")
            
            # Aggregate changed files across commits
            all_files = set()
            for commit in commits:
                all_files.update(commit.get("added", []))
                all_files.update(commit.get("modified", []))
                all_files.update(commit.get("removed", []))

            files_list = list(all_files)

            # Rule 1: Ignore trivial changes (< 3 files)
            if len(files_list) < 3:
                return NormalizedEvent(
                    is_interesting=False,
                    event_type="push",
                    repository=repo_name,
                    ref_or_version=ref,
                    headline="Trivial push ignored",
                    rationale=f"Only {len(files_list)} file(s) modified.",
                    modified_files=files_list,
                )

            # Rule 2: Ignore documentation only changes
            doc_extensions = (".md", ".txt", ".rst", ".adoc", ".png", ".jpg", ".jpeg")
            if all(f.lower().endswith(doc_extensions) for f in files_list):
                return NormalizedEvent(
                    is_interesting=False,
                    event_type="push",
                    repository=repo_name,
                    ref_or_version=ref,
                    headline="Documentation-only push ignored",
                    rationale="All modified files are documentation or images.",
                    modified_files=files_list,
                )

            # Rule 3: Check for Benchmarks
            if any(any(kw in f.lower() for kw in self.BENCHMARK_KEYWORDS) for f in files_list):
                return NormalizedEvent(
                    is_interesting=True,
                    event_type="benchmark_update",
                    repository=repo_name,
                    ref_or_version=ref,
                    headline=f"Engineering Benchmark Update in {repo_name}",
                    rationale="Detected modifications to performance benchmarks or test suites.",
                    modified_files=files_list,
                    category="benchmark",
                )

            # Rule 4: Check for Terraform / IaC changes
            if any(any(f.lower().endswith(kw) for kw in self.IAC_KEYWORDS) for f in files_list):
                return NormalizedEvent(
                    is_interesting=True,
                    event_type="iac_update",
                    repository=repo_name,
                    ref_or_version=ref,
                    headline=f"Infrastructure Topology Shift in {repo_name}",
                    rationale="Detected changes to Terraform, OpenTofu, or Kubernetes definitions.",
                    modified_files=files_list,
                    category="architecture",
                )

            # Rule 5: Check for Security / Policy changes
            if any(any(kw in f.lower() for kw in self.SECURITY_KEYWORDS) for f in files_list):
                return NormalizedEvent(
                    is_interesting=True,
                    event_type="security_policy_update",
                    repository=repo_name,
                    ref_or_version=ref,
                    headline=f"Security Policy Hardening in {repo_name}",
                    rationale="Detected policy-as-code or security compliance modifications.",
                    modified_files=files_list,
                    category="security",
                )

        return NormalizedEvent(
            is_interesting=False,
            event_type=event_type,
            repository=repo_name,
            ref_or_version="n/a",
            headline="Standard event without editorial threshold match",
            rationale="Did not trigger benchmark, IaC, release, or security rules.",
        )
