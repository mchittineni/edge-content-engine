# Runbook: Roll back a bad release

**Trigger:** A released version is causing incorrect output, data loss, cost
overrun, or a security exposure.

## 1. Stop the bleeding first (minutes)

Reverting code takes longer than disabling the thing that is running.

```bash
# Halt the scheduled discovery run so it stops consuming budget/API quota
gh workflow disable "Scheduled Daily Discovery"
```

If the API is deployed, scale the service to zero or route traffic away from it
before doing anything else.

## 2. Decide: revert or fix forward

| Situation | Action |
| --- | --- |
| Cause is known and the fix is one line | Fix forward — faster than a revert cycle |
| Cause unknown, or the blast radius is growing | Revert to the last good tag |
| Data is being corrupted | Revert immediately, diagnose afterwards |

## 3. Revert

```bash
git checkout main && git pull
git revert --no-commit <first-bad-sha>..<last-bad-sha>
git commit -m "revert: roll back vX.Y.Z (<one-line reason>)"
```

Open it as a PR. It still goes through the quality gate — a rollback that
breaks the build is not a rollback. Then cut a patch release
(`docs/runbooks/release.md`) so the released artifact matches `main`.

## 4. Verify

- [ ] The failing behaviour is gone on the new version.
- [ ] `edge list` returns the expected articles and none are in a stuck state.
- [ ] Re-enable what you disabled: `gh workflow enable "Scheduled Daily Discovery"`.

## 5. Write it up

Add an entry to `docs/backlog.md` describing what let the bad release through,
and add the test or gate that would have caught it. A rollback without that
step guarantees a repeat.
