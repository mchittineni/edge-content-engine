variable "environment" {
  description = "Target deployment environment (e.g. prod, staging, dev)"
  type        = string
  default     = "prod"
}

variable "enable_intelligent_tiering" {
  description = "Whether to transition older content lake objects to Intelligent-Tiering"
  type        = bool
  default     = true
}

variable "noncurrent_version_retention_days" {
  description = "Days before noncurrent object versions are permanently expired"
  type        = number
  default     = 90
}
