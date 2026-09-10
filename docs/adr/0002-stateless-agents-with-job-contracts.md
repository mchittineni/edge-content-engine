# 0002. Stateless agents coordinated by JobContract

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** @mchittineni

## Context

The pipeline runs thirteen distinct editorial steps (discovery through
analytics). Each step calls an LLM, can fail transiently, and costs money.
We need retries that do not duplicate spend, and we need to run steps on a
queue rather than in one long-lived process.

## Decision

Every agent subclasses `BaseAgent` and implements a single pure-ish method,
`process(article_id, input_payload) -> output_payload`. Agents hold no state
between jobs. All coordination data travels in a `JobContract` (`packages/schemas/job.py`):
agent type, payloads, attempt count, status, and latency metadata.

`BaseAgent.execute_job` owns the lifecycle — timing, status transitions, and a
deliberately broad `except Exception` that converts any agent failure into
`FAILED`, or `DEAD_LETTER` once `attempt >= max_attempts`.

## Consequences

### Positive
- Any agent can run on any worker; scaling is horizontal by default.
- Retry and dead-letter policy lives in exactly one place.
- Agents are trivial to test: construct a `JobContract`, assert on the result.

### Negative / Accepted costs
- The broad `except Exception` in `BaseAgent.execute_job` is a lint exception
  (`BLE001`) that we justify rather than remove: a worker that crashes on one
  bad agent is worse than one that dead-letters the job. It logs with
  `logger.exception` so nothing is swallowed silently.
- Passing state through payload dictionaries is weakly typed at the boundary,
  mitigated by validating into Pydantic models inside each agent.

### Neutral
- `AgentType.GITHUB_EVENT` has no dispatcher entry because it is handled by the
  webhook route, not by an agent. See `docs/backlog.md` (SDLC-1) for the
  reliability gap this currently leaves.

## Alternatives considered

### Stateful, long-lived agent objects
Rejected: caching model clients inside agents saves little and makes the
retry story ambiguous — a half-mutated agent cannot be safely retried.

### A workflow engine (Temporal, Airflow, Step Functions)
Rejected for now as disproportionate to a single-maintainer project, and it
would put the orchestrator outside the repository's own test suite.
