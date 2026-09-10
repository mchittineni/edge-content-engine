# Testing Guide

## Running

```bash
make test          # fast run
make test-cov      # with the coverage gate (what CI runs)
pytest tests/test_api.py -k review    # one slice
```

Coverage scope and the `fail_under` threshold live in `pyproject.toml`, so the
local command and CI cannot disagree. See ADR
[0004](adr/0004-enforced-quality-gates.md).

## Layout

| File | Covers |
| --- | --- |
| `test_schemas.py` | Pydantic contracts |
| `test_normalizer.py` | GitHub event filtering |
| `test_storage_lake.py` | Content lake + **path-traversal security regressions** |
| `test_api.py` | FastAPI routes, error paths, path-param validation |
| `test_cli.py` | Click commands via `CliRunner` |
| `test_agents.py` | `BaseAgent` lifecycle, retry/dead-letter, dispatcher wiring |
| `test_worker_runner.py` | Worker loop and graceful shutdown |
| `test_llm_budget.py` | Budget enforcement, model routing |
| `test_clients.py` | GitHub/Beehiiv clients (network stubbed) |
| `test_validator.py` | Code-block validation |
| `test_pipeline.py` | End-to-end orchestration |
| `test_observability.py` | Cost reporting |
| `test_packaging.py` | Wheel contents and version-config consistency |

## Rules

**No network. Ever.** `tests/conftest.py` isolates the environment, and client
tests stub `httpx.AsyncClient` with `MockTransport`. A test that reaches
`api.github.com` is a broken test, not a slow one.

**No writes outside the temp lake.** The autouse `isolated_test_env` fixture
gives every test a throwaway directory *and repoints the shared `default_lake`
singleton at it*. Repointing the object's `base_dir` (rather than rebinding the
name per module) is what makes isolation hold — agents reached through the
pipeline hold their own reference to that same object, and previously wrote
real files into the repository's `content/`.

After any test run, `git status content/` must be clean. If it is not, isolation
has regressed.

**Warnings are errors.** A new `DeprecationWarning` from our own code fails the
run. Third-party warnings are allow-listed by message in `pyproject.toml`.

**Security tests are load-bearing.** The parametrised traversal payloads in
`test_storage_lake.py` guard commits `63ab3cc`, `d60c5eb`, `3fd48af`, `49721f5`.
Do not delete them without replacing the control they cover.

## Fixtures

Defined in `tests/conftest.py`: `isolated_test_env`, `mock_lake`,
`sample_article_record`, `sample_article_draft`, `sample_job_contract`,
`sample_opportunity_score`.

## Markers

`unit`, `integration`, `e2e` — declared in `pyproject.toml`. `--strict-markers`
means a typo in a marker name fails the run.

## Writing a new test

1. Assert on behaviour, not formatting. CLI tests check exit codes and key
   substrings, so terminal styling can change freely.
2. Cover the error path. Most defects here have lived in `except` branches.
3. When patching `default_lake`, patch **every** module that imported it —
   it is an import-time singleton (ADR [0003](adr/0003-content-lake-storage-abstraction.md)).
