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

# ECS Fargate Cluster, ECR Repository, and Task Definitions

# 1. Private Elastic Container Registry (ECR)
resource "aws_ecr_repository" "app_repo" {
  name                 = "edge-content-engine"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "edge-content-engine"
    Project     = "EDGE"
    Environment = var.environment
  }
}

# Retain only the last 15 tagged images to manage storage costs
resource "aws_ecr_lifecycle_policy" "repo_policy" {
  repository = aws_ecr_repository.app_repo.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 15 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 15
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# 2. ECS Fargate Cluster with Container Insights
resource "aws_ecs_cluster" "cluster" {
  name = "edge-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "edge-cluster-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
  }
}

# 3. CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/ecs/edge-api-${var.environment}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Project     = "EDGE"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "worker_logs" {
  name              = "/ecs/edge-worker-${var.environment}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Project     = "EDGE"
    Environment = var.environment
  }
}

# 4. Task Definition: FastAPI Server
resource "aws_ecs_task_definition" "api_task" {
  family                   = "edge-api-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.api_cpu)
  memory                   = tostring(var.api_memory)
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${aws_ecr_repository.app_repo.repository_url}:${var.image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "EDGE_ENV", value = var.environment },
        { name = "S3_CONTENT_BUCKET", value = var.content_lake_bucket_name }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])

  tags = {
    Project     = "EDGE"
    Environment = var.environment
  }
}

# 5. Task Definition: Asynchronous Multi-Agent Worker
resource "aws_ecs_task_definition" "worker_task" {
  family                   = "edge-worker-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.worker_cpu)
  memory                   = tostring(var.worker_memory)
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${aws_ecr_repository.app_repo.repository_url}:${var.image_tag}"
      essential = true
      command   = ["python", "-m", "apps.workers.runner"]
      environment = [
        { name = "EDGE_ENV", value = var.environment },
        { name = "S3_CONTENT_BUCKET", value = var.content_lake_bucket_name }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])

  tags = {
    Project     = "EDGE"
    Environment = var.environment
  }
}
