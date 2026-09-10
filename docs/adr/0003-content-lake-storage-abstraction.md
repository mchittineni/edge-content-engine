# 0003. Filesystem/S3 content lake behind one abstraction

- **Status:** Accepted
- **Date:** 2026-09-10
- **Deciders:** @mchittineni

## Context

Articles accumulate immutable artifacts — raw source captures, research,
drafts per version, diagrams, published records, analytics, and state. Local
development must work with no AWS credentials, while production stores the
same artifacts in S3.

Article ids and source ids originate from untrusted input (GitHub webhook
payloads, CLI arguments, API path parameters). They are used to build file
paths, which is a direct path-traversal exposure (CWE-22 / CWE-73).

## Decision

`packages/storage/lake.py` exposes one `ContentLake` class over both backends,
selected by `EDGE_ENV` and `S3_CONTENT_BUCKET`. Every write routes through
`_resolve_safe_path`, which rejects any filename that is not a bare
`[A-Za-z0-9_.-]+` basename and re-checks the resolved absolute path against
the target directory.

`_resolve_safe_path` uses `os.path.basename` / `os.path.abspath` rather than
`pathlib`. This is deliberate: CodeQL's taint analysis recognises those
functions as path sanitizers and does not recognise the `pathlib` equivalents.
Rewriting them to `pathlib` reintroduces the CodeQL alert even though the
behaviour is identical, so `PTH100`/`PTH118`/`PTH119` are ignored for this file
in `pyproject.toml`.

## Consequences

### Positive
- Local and production code paths are identical, so tests exercise the real one.
- Path traversal is blocked in one auditable function, covered by parametrised
  regression tests in `tests/test_storage_lake.py`.

### Negative / Accepted costs
- `default_lake` is a module-level singleton constructed at import time. Each
  importing module binds its own reference, so tests must patch every one of
  them (see the `cli_lake` fixture). Dependency injection would be cleaner;
  the singleton is retained for now because changing it touches every call site.
- The S3 path is not yet exercised by tests.

### Neutral
- Adding a new artifact category means adding a subdirectory to the list in
  `ContentLake.__init__`.

## Alternatives considered

### Writing to S3 always, with a local MinIO container for development
Rejected: it makes the test suite depend on a running container, and the
project must stay runnable with zero infrastructure.

### `pathlib`-only implementation
Rejected: see above — it defeats CodeQL's sanitizer recognition for no
behavioural gain.
