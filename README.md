# EDGE Content Engine (`edge-content-engine`)

An autonomous, event-driven engineering-media platform built for the **EDGE** publication on Beehiiv. It turns real GitHub engineering activity, cloud infrastructure developments, and technical benchmarks into peer-reviewed, fact-checked, architecturally illustrated deep-dive articles—with you as the ultimate human approval gate.

---

## Key Highlights

- **Event-Driven & Decoupled**: Stateless agents communicate asynchronously through standard `JobContract` messages via AWS SQS + DLQs (or local queue engine).
- **GitHub Event Normalization**: Webhook filter ignores minor doc edits and triggers research only on meaningful changes (benchmarks, Terraform refactors, security policies, major releases).
- **6-Metric Opportunity Scoring**: Ranks ideas out of 60 points; only ideas scoring $\ge 48$ automatically enter deep research.
- **Hierarchical Research & Claim Matrix**: Categorizes sources (Tier 1 official docs/RFCs/GitHub down to Tier 4). Technical claims require explicit Tier 1-2 evidence citations.
- **Architecture Diagram Synthesis**: Generates cloud architecture diagrams (Mermaid, SVG, ASCII), integrating with your `tf-arch-diagram-generator`.
- **Rigorous Technical QA & Code Sandbox**: Runs real linters (`terraform validate`, `tflint`, `ruff`, `eslint`, `checkov`). Articles scoring $<90$ are automatically returned for revisions.
- **Model Gateway & Budget Caps**: Task-based LLM routing (cheap models for discovery/SEO, reasoning models for QA, strong models for writing) with hard per-article budget limits ($2.50 max).
- **Interactive Human Gate**: Review articles via rich terminal TUI (`edge review <id>`) or web dashboard (`review.edgeinfra.dev`).
- **Async Beehiiv Publishing**: Polls Beehiiv's v2 API while storing canonical Markdown, HTML, and diagrams in an immutable S3 Content Lake.
- **Authentic Social Distribution**: Tailored posts for LinkedIn, authentic discussion-prompt Reddit posts (anti-spam), and visual X threads.

---

## Architecture Overview

```
GitHub / Sources ─► Normalizer ─► SQS ─► Discovery / Scorer (>=48)
                                           │
                                           ▼
                                 Researcher Agent (Tier 1-3)
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
                 Architect Agent                         Writer Agent
             (Mermaid / tf-arch)                     (14-step template)
                        └──────────────────┬──────────────────┘
                                           ▼
                                Fact-Checker & Validator
                                (terraform / ruff / checkov)
                                           │ (Score >= 90)
                                           ▼
                                       SEO Agent
                                           │
                                           ▼
                              [ HUMAN APPROVAL GATE ]
                                (review.edgeinfra.dev)
                                           │ (Approved)
                                           ▼
                                 Beehiiv API Publisher
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                    LinkedIn             Reddit               X
```

---

## Directory Structure

```
edge-content-engine/
├── apps/
│   ├── api/             # FastAPI webhook & review REST endpoints
│   ├── reviewer/        # Next.js web approval dashboard
│   └── workers/         # Decoupled SQS / local queue worker dispatcher
├── agents/              # Discovery, Scorer, Researcher, Architect, Writer,
│                        # Factchecker, Validator, SEO, Publisher, Social, Analytics
├── packages/
│   ├── schemas/         # Typed Pydantic v2 state & job contracts
│   ├── llm/             # Multi-provider gateway & cost budget enforcer
│   ├── github/          # GitHub App client & webhook event normalizer
│   ├── beehiiv/         # Async Beehiiv v2 API client
│   ├── storage/         # Dual S3 / Local filesystem content lake
│   └── observability/   # OpenTelemetry tracing & cost accounting
├── prompts/             # Version-controlled prompt library (v1, v2...)
├── infrastructure/      # Production Terraform modules (AWS SQS, ECS, S3, Aurora, IAM)
└── content/             # Local content lake (raw, research, drafts, published)
```

---

## Quickstart

### 1. Setup Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

### 2. Run CLI Pipeline
```bash
# Discover candidates from GitHub & ecosystems
edge discover

# Score backlog ideas
edge score

# Run full pipeline for an article
edge pipeline run EDGE-2026-001

# Open interactive human approval dashboard
edge review EDGE-2026-001

# Publish approved article to Beehiiv & social package
edge publish EDGE-2026-001
```

### 3. Start Local Webhook API & Workers
```bash
# Worker event dispatcher
python -m apps.workers.runner

# API Server
uvicorn apps.api.main:app --reload --port 8000
```

---

## SDLC & Quality Standards

This project adheres to strict software development lifecycle (SDLC) standards:

- **Quality & Static Analysis**: Enforced via Ruff, strict Mypy, Bandit SAST, and Pytest test coverage.
- **Git Hooks**: Pre-commit hooks (`.pre-commit-config.yaml`) run formatting, linting, and secret detection before every commit.
- **CI/CD Quality Gates**: GitHub Actions run automated linting, type checks, security scanning (CodeQL + pip-audit), multi-python test matrix (3.11 & 3.12), Terraform validation, and container build smoke tests.
- **Semantic Versioning & PR Hygiene**: Conventional Commits specification enforced on PR titles (`feat:`, `fix:`, `chore:`) with automated release drafting.
- **Containerization**: Multi-stage, non-root `Dockerfile`, `docker-compose.yml`, and `.devcontainer/` specification for VS Code / GitHub Codespaces.

### Common Developer Commands
```bash
make help             # Show all available developer commands
make dev-setup        # Bootstrap virtualenv, install dependencies, and install pre-commit hooks
make lint             # Check code formatting and linting rules
make format           # Automatically format code using Ruff
make typecheck        # Run Mypy static type checking
make security-check   # Run Bandit SAST and pip-audit vulnerability scanner
make test-cov         # Run tests with code coverage metrics
make docker-up        # Start containerized local stack (API + Worker)
```

For full guidelines on branching, PR submission, and definition of done, see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

