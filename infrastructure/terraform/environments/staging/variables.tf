variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "github_repo" {
  description = "GitHub repository formatted as 'owner/repo' for OIDC trust relationship"
  type        = string
  default     = "mchittineni/edge-content-engine"
}

variable "github_branches" {
  description = "Allowed branches for GitHub Actions OIDC role assumption"
  type        = list(string)
  default     = ["staging", "main"]
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "staging"
}
