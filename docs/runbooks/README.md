# Runbooks

Operational procedures for when something is broken or needs to ship. Each
runbook states its trigger, the steps, and how to verify the fix worked.

| Runbook | Use when |
| --- | --- |
| [release.md](release.md) | Cutting a versioned release |
| [rollback.md](rollback.md) | A release is bad and must be undone |
| [pipeline-failure.md](pipeline-failure.md) | An article pipeline run failed or stalled |
| [secret-rotation.md](secret-rotation.md) | A credential leaked or is due for rotation |
| [ci-failure.md](ci-failure.md) | CI is red and the cause is not obvious |
| [terraform-deploy.md](terraform-deploy.md) | Applying or destroying infrastructure |
