variable "environment" {
  description = "Target deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout in seconds for agent queues (defaults to 5 minutes for long LLM runs)"
  type        = number
  default     = 300
}

variable "message_retention_seconds" {
  description = "Standard message retention in seconds (default: 1 day)"
  type        = number
  default     = 86400
}

variable "dlq_message_retention_seconds" {
  description = "DLQ message retention in seconds (default: 14 days)"
  type        = number
  default     = 1209600
}

variable "max_receive_count" {
  description = "Number of retry attempts before routing to the DLQ"
  type        = number
  default     = 3
}

variable "alarm_sns_topic_arn" {
  description = "Optional SNS topic ARN for forwarding CloudWatch DLQ alarms"
  type        = string
  default     = null
}
