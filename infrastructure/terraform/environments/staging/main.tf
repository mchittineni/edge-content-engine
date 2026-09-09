# Root Staging Environment Composition
# EDGE Content Engine

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "EDGE"
      ManagedBy   = "Terraform"
      Environment = "staging"
    }
  }
}

# 1. Immutable S3 Content Lake (Staging)
module "s3" {
  source                     = "../../modules/s3"
  environment                = "staging"
  enable_intelligent_tiering = false
}

# 2. Decoupled Asynchronous SQS Pipeline (Staging)
module "sqs" {
  source      = "../../modules/sqs"
  environment = "staging"
}

# 3. AWS Secrets Manager for Staging
module "secrets" {
  source      = "../../modules/secrets"
  environment = "staging"
}

# 4. Least-Privilege IAM Roles & Scoped GitHub Actions OIDC (Staging)
module "iam" {
  source                  = "../../modules/iam"
  environment             = "staging"
  github_repo             = var.github_repo
  github_branches         = var.github_branches
  content_lake_bucket_arn = module.s3.bucket_arn
  sqs_queue_arns          = values(module.sqs.queue_arns)
  secrets_kms_key_arn     = module.secrets.kms_key_arn
  secret_arns             = values(module.secrets.secret_arns)
}

# 5. ECS Fargate Compute, Container Registry, and Tasks (Staging)
module "ecs" {
  source                   = "../../modules/ecs"
  environment              = "staging"
  execution_role_arn       = module.iam.ecs_execution_role_arn
  task_role_arn            = module.iam.worker_task_role_arn
  content_lake_bucket_name = module.s3.bucket_name
  image_tag                = var.image_tag
}
