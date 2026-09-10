# Runbook: Deploy and tear down infrastructure

Infrastructure changes go through `Terraform Apply` / `Terraform Destroy`
(`workflow_dispatch` only). There is no automatic apply on merge — infrastructure
changes are deliberate acts.

## One-time repository setup

Both workflows authenticate to AWS with OIDC (`aws_iam_openid_connect_provider.github`
in `modules/iam`). No static AWS keys exist or should be created.

**Secrets** (Settings → Secrets and variables → Actions → Secrets):

| Secret | Value |
| --- | --- |
| `AWS_DEPLOY_ROLE_ARN` | `arn:aws:iam::<account>:role/edge-github-actions-<env>` |

**Variables** (same page → Variables):

| Variable | Example |
| --- | --- |
| `AWS_REGION` | `us-east-1` |
| `TF_STATE_BUCKET` | `edge-tf-state-prod` |
| `TF_LOCK_TABLE` | `edge-tf-locks-prod` |

**Environments** (Settings → Environments) — the approval gates live here, not
in the workflow files:

| Environment | Required reviewers |
| --- | --- |
| `staging` | optional |
| `prod` | **required** |
| `staging-destroy` | **required** |
| `prod-destroy` | **required** |

The state bucket and lock table must exist before the first run. They cannot be
managed by the same state they store — create them once by hand or with a
separate bootstrap configuration.

## Apply

1. Actions → **Terraform Apply** → Run workflow.
2. Choose `environment` and, if deploying a new image, `image_tag`.
3. The `plan` job runs `fmt`, `validate`, and `plan -detailed-exitcode`.
   - **No changes** → the run stops. Nothing to approve.
   - **Changes** → the plan is printed to the job summary and uploaded.
4. Review the plan in the job summary, then approve the `apply` job.
5. `apply` runs the **saved plan file** — not a fresh plan — so what was
   approved is exactly what runs.

### Verification

- [ ] `apply` job green; outputs recorded in the run summary.
- [ ] `/healthz` responds on the deployed service.
- [ ] Re-running `Terraform Apply` reports **no changes** (state matches reality).

## Destroy

Destroy deletes the S3 content lake. Confirm the data is expendable or backed up.

1. Actions → **Terraform Destroy** → Run workflow.
2. Fill in:
   - `environment`
   - `confirmation` — exactly `destroy-<environment>` (e.g. `destroy-staging`).
     A mismatch fails the `guard` job before any AWS call.
   - `reason` — recorded in the run log.
3. Review the destroy plan in the job summary. **It lists every resource that
   will be deleted.** Read it.
4. Approve the `destroy` job on the `<env>-destroy` environment.

### Verification

- [ ] `terraform plan` on the environment shows no managed resources remaining.
- [ ] The state object in `TF_STATE_BUCKET` is empty of resources (the file remains).
- [ ] AWS console confirms the ECS service, SQS queues, and S3 bucket are gone.

## If a run fails mid-apply

Terraform state may be partially advanced. Do **not** re-run blindly.

1. Check whether the state lock was released. If a run was cancelled, the
   DynamoDB lock can persist:
   ```bash
   terraform force-unlock <LOCK_ID>   # only when certain no apply is running
   ```
2. Re-run `Terraform Apply` and read the new plan — it reconciles from actual state.
3. If state and reality have diverged, `terraform import` the orphaned resource
   rather than deleting it by hand.

Never edit state files directly.
