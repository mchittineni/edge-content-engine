variable "environment" {
  description = "Target deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "execution_role_arn" {
  description = "ARN of the ECS Task Execution Role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the ECS Task Role"
  type        = string
}

variable "content_lake_bucket_name" {
  description = "Name of the S3 content lake bucket"
  type        = string
}

variable "api_cpu" {
  description = "CPU units for API task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory for API task (in MiB)"
  type        = number
  default     = 1024
}

variable "worker_cpu" {
  description = "CPU units for Worker task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "worker_memory" {
  description = "Memory for Worker task (in MiB)"
  type        = number
  default     = 2048
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "latest"
}
