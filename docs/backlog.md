# Engineering Backlog

Known gaps, each with the evidence that found it. Items are removed only when
fixed *and* covered by a test or gate that would catch a regression.

---

## SDLC-1 — Unmapped agent type crashes the worker loop

- **Severity:** Medium (reliability)
- **Found by:** `tests/test_agents.py::TestDispatcher::test_unmapped_agent_type_raises_clear_error`

`AgentType.GITHUB_EVENT` is a valid enum member with no entry in
`AgentDispatcher.agents`. `AgentDispatcher.dispatch` raises `ValueError` for it.

That `ValueError` is raised *outside* `BaseAgent.execute_job`, so it is not
caught by the agent failure boundary that turns errors into `FAILED` /
`DEAD_LETTER`. A queued job with `agent=github_event` therefore propagates out
of `WorkerRunner.process_single_job` and terminates the worker loop instead of
dead-lettering one job.

**Suggested fix:** catch unknown agent types in `WorkerRunner.process_single_job`
and dead-letter the job, or make `dispatch` return a `DEAD_LETTER` contract
rather than raising. The current behaviour is pinned by a test so the fix is a
deliberate change, not an accident.

---

## SDLC-2 — API has no authentication or webhook signature verification

- **Severity:** High if exposed publicly
- **Found by:** review while writing `tests/test_api.py`

`POST /api/v1/articles/{id}/review` mutates editorial state and
`POST /api/v1/webhooks/github` accepts any JSON body. Neither authenticates the
caller, and the GitHub webhook does not verify the `X-Hub-Signature-256` HMAC.

Anyone who can reach the service can approve or reject articles, and can forge
webhook deliveries.

**Suggested fix:** verify the GitHub HMAC signature against a shared secret, and
put the review endpoints behind an auth dependency before the service is exposed
beyond localhost.

---

## SDLC-3 — CORS allows every origin while also allowing credentials

- **Severity:** Medium
- **Found by:** review of `apps/api/main.py`

The `CORSMiddleware` is configured with `allow_origins=["*"]` together with
`allow_credentials=True`. That combination is rejected by browsers and signals
the intent to accept credentialed cross-origin requests from anywhere.

**Suggested fix:** enumerate the real allowed origins, or set
`allow_credentials=False` if no credentialed cross-origin access is needed.

---

## SDLC-4 — S3 backend of the content lake is untested

- **Severity:** Low
- **Found by:** coverage review

`ContentLake.is_s3` is exercised, but no test covers actual S3 reads or writes.
The production storage path is effectively unverified.

**Suggested fix:** add `moto`-backed tests for the S3 branch.

---

## SDLC-5 — Container smoke test unverified locally

- **Severity:** Low
- **Found by:** authoring `.github/workflows/ci.yml`

The `container` job's smoke test (`import apps.api.main`, `edge --help`) was
written but never executed locally, because no Docker daemon was available on
the authoring machine. It is expected to pass but should be confirmed on the
first CI run.
