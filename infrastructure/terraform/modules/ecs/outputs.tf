output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.cluster.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.cluster.arn
}

output "ecr_repository_url" {
  description = "URL of the private ECR repository"
  value       = aws_ecr_repository.app_repo.repository_url
}

output "api_task_definition_arn" {
  description = "ARN of the API task definition"
  value       = aws_ecs_task_definition.api_task.arn
}

output "worker_task_definition_arn" {
  description = "ARN of the Worker task definition"
  value       = aws_ecs_task_definition.worker_task.arn
}
