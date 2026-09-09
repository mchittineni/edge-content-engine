output "content_lake_bucket" {
  description = "Staging S3 content lake bucket name"
  value       = module.s3.bucket_name
}

output "content_lake_bucket_arn" {
  description = "Staging S3 content lake bucket ARN"
  value       = module.s3.bucket_arn
}

output "sqs_queues" {
  description = "Staging agent queue ARNs"
  value       = module.sqs.queue_arns
}

output "github_actions_role_arn" {
  description = "IAM Role ARN for GitHub Actions OIDC assumption"
  value       = module.iam.github_actions_role_arn
}

output "ecs_cluster_name" {
  description = "Staging ECS Fargate cluster name"
  value       = module.ecs.cluster_name
}

output "ecr_repository_url" {
  description = "Staging ECR repository URL"
  value       = module.ecs.ecr_repository_url
}
