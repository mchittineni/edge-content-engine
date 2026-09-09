output "github_actions_role_arn" {
  description = "ARN of the IAM role assumed by GitHub Actions via OIDC"
  value       = aws_iam_role.github_actions_role.arn
}

output "ecs_execution_role_arn" {
  description = "ARN of the ECS Task Execution Role (for image pulling and secrets injection)"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "worker_task_role_arn" {
  description = "ARN of the ECS Task Role assumed by running worker/API containers"
  value       = aws_iam_role.worker_task_role.arn
}
