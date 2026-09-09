# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
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
