# 0004. Enforced, non-bypassable quality gates

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** @mchittineni

## Context

The repository declared a 70% coverage floor in `pyproject.toml`, but CI ran
`pytest --cov=packages --cov=agents` — a narrower scope than the declared one.
That reported 76% while true full-scope coverage was 58.8%, with `apps/api`,
`cli/`, and `packages/observability` at 0%. The gate existed and was green, and
was measuring the wrong thing.

This is the general failure mode for quality gates: the gate and the thing it
claims to protect drift apart, and the green check hides it.

## Decision

1. **Configuration is the single source of truth.** Coverage scope, the
   fail-under threshold, bandit skips, and warning filters live in
   `pyproject.toml`. CI invokes the tool with no overriding flags, so
   `make test-cov` locally and CI cannot disagree.
2. **Coverage is ratcheted, never lowered.** `fail_under` moves up as coverage
   improves. Lowering it to make a build pass is prohibited.
3. **Warnings are errors** (`filterwarnings = ["error", ...]`). Third-party
   deprecations we cannot fix are allow-listed individually by message, so the
   list stays short and reviewable.
4. **One required status check.** The `quality-gate` job in `ci.yml` depends on
   every other job and fails if any did not succeed. Branch protection requires
   only that job, so adding a new CI job is automatically covered without
   touching repository settings.
5. **Type checking is `--strict`.** The codebase passes it today; keeping it
   strict is cheaper than regaining it later.
6. **Supported Python versions are 3.13 and 3.14**, tested as a matrix.
   `requires-python`, the ruff `target-version`, and the mypy `python_version`
   must agree - `tests/test_packaging.py` asserts it, because a ruff target
   below `requires-python` silently permits syntax the project cannot run.

## Consequences

### Positive
- The number on the badge is the number that is true.
- A new CI job cannot be accidentally left out of branch protection.

### Negative / Accepted costs
- Strict mypy and warnings-as-errors mean an upstream dependency's deprecation
  can break CI on a day we changed nothing. The allow-list is the release valve.
- Full-scope coverage made the reported number drop before it rose; that is the
  point.

### Neutral
- Local hook versions in `.pre-commit-config.yaml` must be kept in step with the
  versions resolved from `[project.optional-dependencies].dev`.

## Alternatives considered

### Coverage reporting without a failing threshold
Rejected: an advisory number trends downward. A threshold that fails the build
is the only kind that holds.

### Listing every CI job in branch protection
Rejected: it is a second place to remember, and the one that gets forgotten.
