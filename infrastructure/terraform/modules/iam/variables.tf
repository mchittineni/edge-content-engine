variable "environment" {
  description = "Target deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "github_repo" {
  description = "GitHub repository formatted as 'owner/repo' for OIDC trust relationship"
  type        = string
  default     = "mchittineni/edge-content-engine"
}

variable "github_branches" {
  description = "Allowed branches for GitHub Actions OIDC role assumption"
  type        = list(string)
  default     = ["main"]
}

variable "content_lake_bucket_arn" {
  description = "ARN of the S3 content lake bucket for least-privilege IAM scoping"
  type        = string
}

variable "sqs_queue_arns" {
  description = "List of SQS queue ARNs for least-privilege worker policy scoping"
  type        = list(string)
  default     = []
}

variable "secrets_kms_key_arn" {
  description = "ARN of the KMS key used for secret encryption"
  type        = string
  default     = "*"
}

variable "secret_arns" {
  description = "List of Secrets Manager ARNs for secret retrieval permissions"
  type        = list(string)
  default     = []
}
