terraform {
  required_version = ">= 1.9.0"

  # Must match the constraint in every consuming environment, otherwise a
  # standalone `terraform validate` of this module resolves a different
  # provider major version and reports errors the environments never see.
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Secrets Manager with KMS Encryption for LLM & Publishing Credentials

# 1. KMS Customer Managed Key for Secrets
resource "aws_kms_key" "secrets_key" {
  description             = "KMS Key for EDGE Content Engine secrets encryption in ${var.environment}"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "edge-secrets-key-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "secrets_key_alias" {
  name          = "alias/edge-secrets-${var.environment}"
  target_key_id = aws_kms_key.secrets_key.key_id
}

# 2. Managed Secrets for API Providers & Platform Integrations
locals {
  secret_names = [
    "gemini-api-key",
    "openai-api-key",
    "anthropic-api-key",
    "beehiiv-api-token",
    "github-app-credentials",
    "social-api-credentials"
  ]
}

resource "aws_secretsmanager_secret" "secrets" {
  for_each                = toset(local.secret_names)
  name                    = "edge/${var.environment}/${each.key}"
  description             = "EDGE Content Engine credentials for ${each.key} (${var.environment})"
  kms_key_id              = aws_kms_key.secrets_key.arn
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Project     = "EDGE"
    Environment = var.environment
  }
}
