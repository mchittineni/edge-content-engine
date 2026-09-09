# Least-Privilege IAM Roles & GitHub Actions OIDC Federation

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ==============================================================================
# 1. GitHub OIDC Provider & Deployment Role
# ==============================================================================
resource "aws_iam_openid_connect_provider" "github" {
  count           = var.environment == "prod" ? 1 : 0
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1", "1c58761d6b1075e79981f53f31718add42a3fe04"]
}

data "aws_iam_policy_document" "github_oidc_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    principals {
      type        = "Federated"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = concat(
        [for b in var.github_branches : "repo:${var.github_repo}:ref:refs/heads/${b}"],
        ["repo:${var.github_repo}:ref:refs/tags/*"]
      )
    }
  }
}

resource "aws_iam_role" "github_actions_role" {
  name               = "edge-github-actions-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_assume.json

  tags = {
    Name        = "edge-github-actions-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
  }
}

# Attach scoped CI/CD deployment policy to GitHub Actions
data "aws_iam_policy_document" "github_deploy_policy" {
  statement {
    sid    = "ECRAuth"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ECRPushPull"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = ["arn:aws:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:repository/edge-*"]
  }

  statement {
    sid    = "ECSUpdate"
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "github_actions_deploy" {
  name   = "edge-github-actions-deploy-${var.environment}"
  policy = data.aws_iam_policy_document.github_deploy_policy.json
}

resource "aws_iam_role_policy_attachment" "github_deploy_attach" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = aws_iam_policy.github_actions_deploy.arn
}

# ==============================================================================
# 2. ECS Task Execution Role (Pulls images, streams logs, injects secrets)
# ==============================================================================
resource "aws_iam_role" "ecs_execution_role" {
  name = "edge-ecs-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "edge-ecs-execution-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
  }
}

# Standard AWS managed policy for task execution
resource "aws_iam_role_policy_attachment" "ecs_execution_standard" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Granular inline policy allowing ECS agent to fetch Secrets Manager values & decrypt via KMS
data "aws_iam_policy_document" "secrets_access" {
  statement {
    sid    = "SecretsManagerRead"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = length(var.secret_arns) > 0 ? var.secret_arns : ["*"]
  }

  statement {
    sid    = "KMSDecrypt"
    effect = "Allow"
    actions = [
      "kms:Decrypt"
    ]
    resources = [var.secrets_kms_key_arn]
  }
}

resource "aws_iam_policy" "ecs_secrets_policy" {
  name   = "edge-ecs-secrets-${var.environment}"
  policy = data.aws_iam_policy_document.secrets_access.json
}

resource "aws_iam_role_policy_attachment" "ecs_secrets_attach" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = aws_iam_policy.ecs_secrets_policy.arn
}

# ==============================================================================
# 3. ECS Task Role (Runtime application permissions for worker & API)
# ==============================================================================
resource "aws_iam_role" "worker_task_role" {
  name = "edge-worker-task-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "edge-worker-task-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "worker_task_policy" {
  # S3 Content Lake: Read, write, delete, list within bucket
  statement {
    sid    = "S3ContentLakeAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      var.content_lake_bucket_arn,
      "${var.content_lake_bucket_arn}/*"
    ]
  }

  # SQS Queue Operations: Process and enqueue agent jobs
  statement {
    sid    = "SQSQueueOperations"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:SendMessage",
      "sqs:ChangeMessageVisibility"
    ]
    resources = length(var.sqs_queue_arns) > 0 ? var.sqs_queue_arns : ["*"]
  }

  # CloudWatch / Observability Metrics
  statement {
    sid    = "CloudWatchMetrics"
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricData"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "worker_task_policy" {
  name   = "edge-worker-task-policy-${var.environment}"
  policy = data.aws_iam_policy_document.worker_task_policy.json
}

resource "aws_iam_role_policy_attachment" "worker_task_attach" {
  role       = aws_iam_role.worker_task_role.name
  policy_arn = aws_iam_policy.worker_task_policy.arn
}
