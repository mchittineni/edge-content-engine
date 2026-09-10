# Repository Governance

Settings that live in GitHub rather than in the repository, recorded here so
they are reviewable and restorable.

## Branch protection — `main`

Apply as a ruleset (Settings → Rules → Rulesets) targeting `main`:

| Setting | Value | Why |
| --- | --- | --- |
| Require a pull request | On, 1 approval | No direct pushes |
| Dismiss stale approvals | On | An approval applies to reviewed code only |
| Require review from Code Owners | On | `.github/CODEOWNERS` |
| Require status checks | **`Quality Gate`** only | Aggregates every CI job — see below |
| Require branches up to date | On | Prevents semantic merge breakage |
| Require conversation resolution | On | No silently-dropped review comments |
| Require signed commits | On | Commit authorship is verifiable |
| Require linear history | On | Bisectable |
| Block force pushes | On | History is append-only |
| Restrict deletions | On | |
| Enforce for admins | On | A rule the owner can skip is a suggestion |

### Why only one required check

`ci.yml`'s `quality-gate` job depends on every other job and fails if any of
them did not succeed. Requiring that single check means a newly added CI job is
protected automatically, with no branch-protection edit. Listing jobs
individually creates a second place to remember — and the one that gets
forgotten. See ADR [0004](adr/0004-enforced-quality-gates.md).

Apply with the CLI:

```bash
gh api -X PUT repos/mchittineni/edge-content-engine/branches/main/protection \
  --input docs/branch-protection.json
```

## Repository security settings

Settings → Code security:

- [ ] Dependency graph — **on**
- [ ] Dependabot alerts — **on**
- [ ] Dependabot security updates — **on**
- [ ] Secret scanning — **on**
- [ ] Push protection — **on** (blocks the commit rather than alerting later)
- [ ] Private vulnerability reporting — **on** (matches `SECURITY.md`)
- [ ] CodeQL — configured by `.github/workflows/codeql.yml`

## Actions settings

- Fork pull request workflows: **require approval for all outside collaborators**
- Default `GITHUB_TOKEN` permissions: **read-only** (workflows opt in per job)
- Allow actions: **only actions pinned by SHA** (ADR [0005](adr/0005-pin-all-supply-chain-inputs.md))

## Secrets

| Secret | Used by | Rotation |
| --- | --- | --- |
| `GEMINI_API_KEY` | discovery, pipeline agents | 90 days |
| `BEEHIIV_API_TOKEN` | publisher | 90 days |
| AWS deploy role | Terraform | OIDC, no static keys |

Rotation procedure: [runbooks/secret-rotation.md](runbooks/secret-rotation.md).
