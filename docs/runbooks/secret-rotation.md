# Runbook: Rotate a credential

**Trigger:** Gitleaks or CodeQL flagged a secret, a credential was pasted
somewhere it should not have been, or a scheduled rotation is due.

## If a secret leaked, assume it is compromised

A secret in git history is public the moment the commit is pushed, even if the
repository is private and even after a force-push. **Revoke first, clean up
second.** Cleaning history without revoking accomplishes nothing.

## 1. Revoke immediately

| Secret | Where to revoke |
| --- | --- |
| `GEMINI_API_KEY` | Google AI Studio → API keys → delete |
| `GITHUB_TOKEN` (PAT) | GitHub → Settings → Developer settings → revoke |
| `BEEHIIV_API_TOKEN` | Beehiiv → Settings → API → revoke |
| AWS keys | IAM → deactivate, then delete the access key |

## 2. Issue a replacement

Grant the minimum scope the code actually uses — a leak is the right moment to
discover the old token was over-privileged.

## 3. Update every consumer

```bash
gh secret set GEMINI_API_KEY --body "<new-value>"   # GitHub Actions
```

Then AWS Secrets Manager (`infrastructure/terraform/modules/secrets/`) and your
local `.env`. `.env` is gitignored; confirm it still is.

## 4. Purge from history (only after revoking)

```bash
git log -S '<fragment-of-secret>' --oneline    # find the commits
```

Rewriting published history breaks every clone and does not un-publish the
secret. Prefer leaving it and relying on the revocation. Rewrite only when a
policy requires it, using `git filter-repo`, and tell every collaborator first.

## 5. Verify

- [ ] The old credential returns 401/403 when used.
- [ ] `pre-commit run gitleaks --all-files` is clean.
- [ ] The `Secret Scanning (Gitleaks)` CI job is green on `main`.
- [ ] A pipeline run succeeds with the new credential.
- [ ] Provider access logs show no unrecognised use before revocation.
