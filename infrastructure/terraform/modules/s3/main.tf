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

# S3 Content Lake: Immutable storage for raw sources, research, drafts, and diagrams

resource "aws_s3_bucket" "content_lake" {
  bucket        = "edge-content-lake-${var.environment}"
  force_destroy = var.environment != "prod"

  tags = {
    Name        = "edge-content-lake-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "content_lake_versioning" {
  bucket = aws_s3_bucket.content_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "content_lake_encryption" {
  bucket = aws_s3_bucket.content_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "content_lake_block_public" {
  bucket                  = aws_s3_bucket.content_lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enforce in-transit encryption (TLS 1.2+)
data "aws_iam_policy_document" "enforce_tls" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.content_lake.arn,
      "${aws_s3_bucket.content_lake.arn}/*"
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "content_lake_policy" {
  bucket = aws_s3_bucket.content_lake.id
  policy = data.aws_iam_policy_document.enforce_tls.json
}

# Cost-optimization lifecycle management
resource "aws_s3_bucket_lifecycle_configuration" "content_lake_lifecycle" {
  bucket = aws_s3_bucket.content_lake.id

  rule {
    id     = "intelligent-tiering-and-cleanup"
    status = "Enabled"

    filter {
      prefix = ""
    }

    dynamic "transition" {
      for_each = var.enable_intelligent_tiering ? [1] : []
      content {
        days          = 30
        storage_class = "INTELLIGENT_TIERING"
      }
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_retention_days
    }
  }
}

# CORS for reviewer UI / dashboard diagram access
resource "aws_s3_bucket_cors_configuration" "content_lake_cors" {
  bucket = aws_s3_bucket.content_lake.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://review.edgeinfra.dev", "http://localhost:3000"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}
