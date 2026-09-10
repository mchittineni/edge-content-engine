# Contributing to EDGE Content Engine

Thank you for contributing to the **EDGE Content Engine**! This document defines the engineering standards, workflow, and quality gates that govern this codebase.

---

## 1. Engineering Principles & SDLC Overview

We adhere to modern Software Development Life Cycle (SDLC) standards:
- **Trunk-Based Development**: We maintain a production-ready `main` branch with short-lived feature and fix branches.
- **Strict Quality Gates**: Every pull request must pass static analysis (Ruff), strict type checking (Mypy), security scanning (Bandit, pip-audit), and full test coverage suites.
- **Contract-Driven Architecture**: All inter-agent data passing is governed by Pydantic / SQLModel models (`packages/schemas`). No untyped payloads.
- **Security & Privacy by Default**: Zero secret leaks; non-root container runtimes; dependency vulnerability audits.

---

## 2. Branching & Commit Conventions

### Branch Naming
Branch names should be short, descriptive, and prefixed with the change category:
- `feat/<topic>`: New agent, feature, or platform integration (e.g. `feat/linkedin-auto-publisher`)
- `fix/<issue>`: Bug fixes (e.g. `fix/normalizer-regex-escape`)
- `refactor/<scope>`: Code refactoring without behavioral changes
- `chore/<scope>`: Tooling, dependency updates, CI workflows
- `docs/<topic>`: Documentation updates

### Conventional Commits
All commits and Pull Request titles MUST follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

#### Types:
- `feat`: A new feature or capability
- `fix`: A bug fix
- `docs`: Documentation changes only
- `style`: Formatting changes that do not affect code logic
- `refactor`: Code changes that neither fix a bug nor add a feature
- `perf`: Performance improvements
- `test`: Adding or correcting tests
- `build`: Changes affecting build system or external dependencies
- `ci`: Changes to CI/CD workflows and configuration scripts
- `chore`: Routine maintenance, repo hygiene

*Example:* `feat(agents): add automatic claim verification in researcher`

---

## 3. Local Development Setup

### Prerequisites
- **Python 3.13+** (CI tests 3.13 and 3.14; install via `pyenv` or `homebrew`)
- **Docker & Docker Compose** (for containerized execution)
- **Make**

### Quickstart
1. Clone the repository:
   ```bash
   git clone https://github.com/<org>/edge-content-engine.git
   cd edge-content-engine
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install project and development dependencies in editable mode:
   ```bash
   make install
   ```

4. Install pre-commit hooks:
   ```bash
   make pre-commit-install
   ```

5. Configure your local environment:
   ```bash
   cp .env.example .env
   # Populate GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY as appropriate
   ```

---

## 4. Quality Commands

Before opening a PR, run the local quality checks:

```bash
# Run linting and formatting checks
make lint

# Run automatic formatting
make format

# Run static type checking
make typecheck

# Run security SAST and dependency audits
make security-check

# Run test suite with coverage report
make test-cov
```

---

## 5. Pull Request Process & Definition of Done (DoD)

Before any pull request can be merged into `main`:
1. **Quality Gates Passed**: All GitHub Actions checks (Lint, Mypy, Security, Tests, Terraform, Docker) must pass green.
2. **Code Coverage**: Test suite must maintain minimum 75% coverage across all core packages and agents.
3. **No Secrets**: Confirm no API tokens, AWS keys, or sensitive credentials are committed.
4. **Documentation**: Any new endpoints, schemas, or agent workflows must be reflected in `README.md` or package docstrings.
5. **Code Review**: At least one approving review from a designated code owner (`CODEOWNERS`).
6. **PR Title**: Must follow Conventional Commits formatting so automated changelog generation functions correctly.
