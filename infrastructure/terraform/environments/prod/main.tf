# Root Production Environment Composition
# EDGE Content Engine

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Production remote state backend configuration:
  # backend "s3" {
  #   bucket         = "edge-tf-state-prod"
  #   key            = "edge-content-engine/prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "edge-tf-locks-prod"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "EDGE"
      ManagedBy   = "Terraform"
      Environment = "prod"
    }
  }
}

# 1. Immutable S3 Content Lake
module "s3" {
  source                     = "../../modules/s3"
  environment                = "prod"
  enable_intelligent_tiering = true
}

# 2. Decoupled Asynchronous SQS Pipeline & CloudWatch Alarms
module "sqs" {
  source      = "../../modules/sqs"
  environment = "prod"
}

# 3. AWS Secrets Manager for LLM & Publishing Credentials
module "secrets" {
  source      = "../../modules/secrets"
  environment = "prod"
}

# 4. Least-Privilege IAM Roles & Scoped GitHub Actions OIDC
module "iam" {
  source                  = "../../modules/iam"
  environment             = "prod"
  github_repo             = var.github_repo
  github_branches         = var.github_branches
  content_lake_bucket_arn = module.s3.bucket_arn
  sqs_queue_arns          = values(module.sqs.queue_arns)
  secrets_kms_key_arn     = module.secrets.kms_key_arn
  secret_arns             = values(module.secrets.secret_arns)
}

# 5. ECS Fargate Compute, Container Registry, and Tasks
module "ecs" {
  source                   = "../../modules/ecs"
  environment              = "prod"
  execution_role_arn       = module.iam.ecs_execution_role_arn
  task_role_arn            = module.iam.worker_task_role_arn
  content_lake_bucket_name = module.s3.bucket_name
  image_tag                = var.image_tag
}
