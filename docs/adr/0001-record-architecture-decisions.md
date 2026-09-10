# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** @mchittineni

## Context

This repository is developed largely by one maintainer working with AI agents.
That combination loses context fastest: decisions made in a single session
(why the content lake uses `os.path` instead of `pathlib`, why agents are
stateless) are invisible to the next session and get "helpfully" undone.

Several such decisions already exist in git history only as commit messages —
for example the four commits hardening path traversal in the storage lake.
A commit message is not discoverable when someone is about to change the code.

## Decision

We keep Architecture Decision Records in `docs/adr/`, numbered and immutable
once accepted, using the format in `0000-template.md`. Code that exists because
of an ADR carries a comment pointing at it.

## Consequences

### Positive
- Non-obvious constraints survive context loss.
- Code review can cite a decision instead of relitigating it.

### Negative / Accepted costs
- Writing an ADR costs real time, so the three-part test in `README.md` exists
  to stop this from becoming a diary of every change.

### Neutral
- The index in `docs/adr/README.md` must be updated with each new ADR.

## Alternatives considered

### Long-form comments in the code
Rejected: they document the *what* well but have nowhere to record rejected
alternatives, and they get deleted along with the code they annotate.
