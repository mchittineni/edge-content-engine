# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Architecture Decision Records (`docs/adr/`) covering agent statelessness, the content lake, quality-gate enforcement, and supply-chain pinning.
- Operational runbooks (`docs/runbooks/`) for release, rollback, pipeline failure, secret rotation, CI failure, and Terraform deploy/destroy.
- `docs/architecture.md`, `docs/testing.md`, `docs/repository-governance.md`, and `docs/backlog.md`.
- `Terraform Apply` and `Terraform Destroy` workflows (`workflow_dispatch`, AWS OIDC, plan-then-apply, environment approval gates, typed destroy confirmation).
- Supply-chain security jobs: Gitleaks secret scanning, Trivy IaC and container scanning, CycloneDX SBOM generation, dependency review, and OpenSSF Scorecard.
- Build-provenance attestation and tag/version consistency check in the release workflow.
- Aggregate `Quality Gate` job as the single required status check for branch protection.
- 115 new tests covering the API, CLI, storage lake, agent lifecycle, worker shutdown, budget enforcement, and HTTP clients - including parametrised path-traversal regression tests.
- `LICENSE` (MIT) and `CODE_OF_CONDUCT.md`.
- `make verify`, `make tf-validate`, `make tf-security`, `make secrets-scan`, and `make test-fast` targets.

### Changed
- Coverage now measures `packages`, `agents`, `apps`, and `cli`; the threshold was raised from 70% to 80% (true full-scope coverage rose from 58.8% to 84.7%).
- `mypy` runs in `--strict` mode across all 41 source modules.
- Ruff enforces 28 rule families (security, async correctness, complexity, modernization) instead of 4.
- Pytest treats warnings as errors, with a narrow allow-list for third-party deprecations.
- All GitHub Actions are pinned to full commit SHAs; workflows declare least-privilege `permissions`, timeouts, and `persist-credentials: false`.
- Terraform modules declare `required_providers` (`~> 5.0`) and lock files are committed; both environments use a partial S3 backend.
- Pre-commit adds Gitleaks, actionlint, hadolint, Terraform, and Conventional Commit hooks, with versions aligned to the dev extras.

### Fixed
- Coverage gate measured a narrower scope than it declared, reporting 76% when true coverage was 58.8%.
- `mypy` pre-commit hook reported `import-not-found` instead of real type errors because runtime dependencies were missing from `additional_dependencies`.
- Blocking `subprocess.run` inside the async validator agent replaced with `asyncio.create_subprocess_exec` using a resolved absolute binary path.
- Worker daemon busy-waited on `asyncio.sleep`, delaying shutdown by up to a full poll interval; it now waits on a stop event.
- Silently swallowed exceptions in the content lake and LLM client are now logged with precise exception types.
- Unbounded recursion in the CLI approval gate's draft preview replaced with a loop.
- Deprecated `data.aws_region.current.name` and unpinned provider resolution in Terraform modules.
- `make test` failed with `ModuleNotFoundError` unless the package was installed; `pythonpath` now makes a bare `pytest` work.

### Added (earlier in this cycle)
- Enterprise-grade SDLC framework across repository governance, code quality, and automation.
- Multi-stage CI quality gates in GitHub Actions (lint, typecheck, security SAST, multi-python test matrix, container build smoke tests).
- Pre-commit hooks (`.pre-commit-config.yaml`) with Ruff, Mypy, Bandit, and file hygiene hooks.
- Static analysis & security scanning via Bandit, pip-audit, and GitHub CodeQL.
- Automated Dependabot configuration for `pip`, `github-actions`, and `terraform`.
- Pull request title validation workflow enforcing Conventional Commits.
- Standardized issue forms (`bug_report.yml`, `feature_request.yml`) and PR template.
- Multi-stage non-root `Dockerfile`, `.dockerignore`, `docker-compose.yml`, and `.devcontainer/devcontainer.json`.
- Shared testing fixtures in `tests/conftest.py` with mock LLM and storage lake environments.
- Enriched self-documenting `Makefile`.

---

## [0.1.0] - 2026-09-09

### Added
- Initial core architecture for the autonomous EDGE content engine:
  - 10 specialized agents (Scorer, Researcher, Architect, Writer, Validator, SEO, Social, Factchecker, Analytics, Evergreen).
  - Event-driven ingestion with GitHub webhook normalizer.
  - Pydantic/SQLModel contract-driven inter-agent data passing.
  - Multi-tier LLM routing with budget controller.
  - S3 Content Lake integration and local filesystem fallback.
  - CLI review and interactive approval tool.
  - Terraform infrastructure modules for S3, SQS, and IAM.
