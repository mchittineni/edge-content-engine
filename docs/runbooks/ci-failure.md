# Runbook: CI is red

**Trigger:** The `Quality Gate` check is failing.

## Reproduce locally first

Every CI gate has a local equivalent, and they read their configuration from the
same `pyproject.toml`. If CI fails and local passes, that drift is itself a bug.

```bash
make lint typecheck test-cov security-check
```

## Job-by-job

| Failing job | Local command | Usual cause |
| --- | --- | --- |
| `Lint & Format` | `make lint` | Run `make format` |
| `Strict Type Check` | `make typecheck` | A new function lacks annotations; `mypy` is `--strict` |
| `Tests` | `make test-cov` | A real failure, or coverage fell below `fail_under` |
| `SAST (Bandit)` | `bandit -c pyproject.toml -r packages agents apps cli` | Justify with a targeted `# nosec` and a comment, or fix it |
| `Dependency Vulnerability Audit` | `pip-audit --desc on --strict` | Upgrade the dependency; if there is no fix, document it here |
| `Secret Scanning` | `pre-commit run gitleaks --all-files` | Follow `secret-rotation.md`. Do not just delete the line |
| `Terraform Quality Gate` | `terraform fmt -recursive` then validate per directory | Missing `required_providers`, or a stale `.terraform.lock.hcl` |
| `Container Build` | `docker build -t edge-content-engine:ci .` | Dockerfile or dependency resolution |

## Coverage dropped below the threshold

Add the missing tests. Do **not** lower `fail_under` — see ADR
[0004](../adr/0004-enforced-quality-gates.md). Find the gap with:

```bash
make test-cov     # the term-missing report lists uncovered lines
```

## A dependency deprecation broke the build overnight

`filterwarnings = ["error", ...]` turns new warnings into failures. If the
warning comes from a third-party package and cannot be fixed here, add a
narrow, message-specific `ignore:` entry in `pyproject.toml` — never a blanket
category ignore.

## Only the tag/release build is failing

`Assert tag matches project version` fails when the tag and
`[project].version` disagree. Follow `release.md`; do not move the tag.
