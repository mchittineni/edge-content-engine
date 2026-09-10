# 0005. Pin every supply-chain input by digest

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** @mchittineni

## Context

This repository grants CI credentials (`GEMINI_API_KEY`, `GITHUB_TOKEN`) to
workflows that run third-party code. A mutable reference — `actions/checkout@v4`,
an unpinned Terraform provider — means the code executed with those credentials
can change without any commit to this repository.

The Terraform case was not hypothetical. The modules declared no
`required_providers`, so validating a module standalone resolved AWS provider
v6 while the environments pinned `~> 5.0`. The same `terraform validate` passed
locally and failed in the pre-commit hook, on a real attribute deprecation.

## Decision

- **GitHub Actions** are referenced by full 40-character commit SHA, with the
  human-readable tag in a trailing comment. Dependabot proposes SHA bumps.
- **Terraform providers** are constrained in every module *and* environment,
  and `.terraform.lock.hcl` is committed (explicitly un-ignored in `.gitignore`).
- **Container base images** stay on an explicit tag; image contents are scanned
  by Trivy and inventoried by an SBOM on every build.
- **Python dependencies** are floor-pinned in `pyproject.toml` and audited by
  `pip-audit` against the fully resolved environment, not just the top level.
- Workflows declare least-privilege `permissions` and set
  `persist-credentials: false` on checkout so the token is not left in
  `.git/config` for later steps.

## Consequences

### Positive
- Executed CI code changes only via a reviewable commit.
- IaC validation is reproducible across machines and CI.

### Negative / Accepted costs
- SHA pins are unreadable and need Dependabot to stay current; an unattended
  repository will drift onto stale, unpatched action versions.
- Committed lock files add churn to provider-upgrade pull requests.

### Neutral
- New workflows must follow the pin-and-comment convention; `actionlint` in
  pre-commit catches syntax but not unpinned references, so review must.

## Alternatives considered

### Pinning actions to major tags (`@v5`)
Rejected: tags are mutable. A compromised or force-moved tag executes new code
with our secrets and leaves no trace in this repository.
