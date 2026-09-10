# Runbook: Cut a release

**Trigger:** `main` holds changes ready to ship.

## Preconditions

- [ ] `main` is green (the `Quality Gate` check passed).
- [ ] `CHANGELOG.md` has an `## [Unreleased]` section describing the changes.

## Steps

1. **Choose the version** per [SemVer](https://semver.org/):
   breaking → major, `feat` → minor, `fix`/`chore` → patch.

2. **Bump the version** in `pyproject.toml` (`[project].version`).
   The release workflow fails the build if the tag and this value disagree.

3. **Close the changelog section**: rename `## [Unreleased]` to
   `## [X.Y.Z] - YYYY-MM-DD` and open a fresh empty `## [Unreleased]`.

4. **Open a PR** titled `chore(release): vX.Y.Z`. Merge once green.

5. **Tag the merge commit** on `main`:

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

6. **Watch `Release & Changelog Automation`.** It re-runs the full quality
   gate on the tagged commit, builds the sdist/wheel, generates a CycloneDX
   SBOM, attests build provenance, and publishes the GitHub release.

## Verification

- [ ] The release appears at `/releases` with `dist/*` and `sbom-cyclonedx.json` attached.
- [ ] `gh attestation verify dist/<wheel> --owner mchittineni` succeeds.
- [ ] `pip install` of the published wheel imports cleanly.

## If it fails

The tag is already pushed. Do **not** force-move it — provenance is bound to a
commit. Delete the tag, fix forward on `main`, and tag the new commit:

```bash
git push --delete origin vX.Y.Z && git tag -d vX.Y.Z
```
