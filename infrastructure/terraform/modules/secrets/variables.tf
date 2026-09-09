variable "environment" {
  description = "Target deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "recovery_window_in_days" {
  description = "Number of days that AWS Secrets Manager waits before permanent deletion"
  type        = number
  default     = 0
}
