# EDGE Content Engine - Cloud Infrastructure (Terraform)

Production-grade AWS infrastructure for the **EDGE Content Engine**, architected according to the **AWS Well-Architected Framework**.

---

## 1. Architecture Overview

```
                          ┌───────────────────────────┐
                          │    GitHub Actions CI/CD   │
                          └─────────────┬─────────────┘
                                        │ (OIDC Federated Auth)
                                        ▼
                      ┌───────────────────────────────────┐
                      │    Private ECR Container Image    │
                      └─────────────────┬─────────────────┘
                                        │
                                        ▼
                     ┌─────────────────────────────────────┐
                     │          ECS Fargate Cluster        │
                     │  ┌───────────────┐ ┌──────────────┐ │
                     │  │   edge-api    │ │  edge-worker │ │
                     │  └───────┬───────┘ └───▲──────┬───┘ │
                     └──────────┼─────────────┼──────┼─────┘
                                │             │      │
                                ▼             │      ▼
      ┌──────────────────────────────┐        │    ┌───────────────────────────┐
      │  AWS Secrets Manager + KMS   │        │    │     S3 Content Lake       │
      │  - Gemini / OpenAI API Keys  │        │    │  - Versioned & Encrypted  │
      │  - Beehiiv & Social Tokens   │        │    │  - Intelligent-Tiering    │
      │  - GitHub App Private Key    │        │    │  - In-Transit TLS Enforced│
      └──────────────────────────────┘        │    └───────────────────────────┘
                                              │
                                  ┌───────────┴───────────┐
                                  │      SQS Pipelines    │
                                  │  - SSE Encrypted      │
                                  │  - Paired 14-day DLQs │
                                  │  - CloudWatch Alarms  │
                                  └───────────────────────┘
```

---

## 2. Directory Layout

```
infrastructure/terraform/
├── environments/
│   ├── prod/                        # Production environment composition
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars.example
│   └── staging/                     # Staging environment composition
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars.example
└── modules/
    ├── s3/                          # Immutable Content Lake (TLS 1.2+, Intelligent Tiering)
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── sqs/                         # Multi-agent queues + DLQs + CloudWatch alarms
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── secrets/                     # AWS Secrets Manager with dedicated KMS key
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── iam/                         # Least-privilege roles (GitHub OIDC, ECS Task, Task Execution)
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── ecs/                         # ECS Fargate cluster, ECR repository, and task definitions
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## 3. Modules & Security Features

### `modules/s3`
- **In-Transit Encryption**: Bucket policy explicitly denies any request where `aws:SecureTransport == false`.
- **At-Rest Encryption**: Server-side AES256 encryption.
- **Cost Optimization**: Lifecycle rules automatically transition objects to `INTELLIGENT_TIERING` after 30 days and expire non-current versions after 90 days.
- **Public Access Block**: Strict blocking of all public ACLs and policies.

### `modules/sqs`
- **Encryption**: SSE-SQS enabled across all queues and DLQs.
- **Fault Tolerance**: Paired Dead-Letter Queues with `maxReceiveCount = 3` and 14-day retention.
- **DLQ Redrive Allow Policy**: Limits dead-letter routing exclusively to the designated upstream queue.
- **Observability**: Automatic CloudWatch alarms on every DLQ triggering if `ApproximateNumberOfMessagesVisible > 0`.

### `modules/secrets`
- **KMS Customer Managed Key**: Automatic key rotation enabled.
- **Managed Secrets**: Pre-configured secret containers for `gemini-api-key`, `openai-api-key`, `anthropic-api-key`, `beehiiv-api-token`, `github-app-credentials`, and `social-api-credentials`.

### `modules/iam`
- **GitHub Actions OIDC**: Replaces static AWS access keys with temporary STS credentials; scoped strictly to repository and specific branches (`main`, `staging`) or release tags.
- **Role Separation**:
  - `ecs_execution_role`: Scoped strictly to pulling ECR images, creating CloudWatch log streams, and retrieving/decrypting secrets.
  - `worker_task_role`: Scoped strictly to S3 Content Lake read/write, SQS queue consumption, and emitting CloudWatch metrics.

### `modules/ecs`
- **Fargate Serverless Compute**: Zero EC2 host management.
- **Container Insights**: Enabled on ECS cluster for CPU, memory, and task performance metrics.
- **Private ECR**: Vulnerability scanning on push (`scan_on_push = true`) and lifecycle policy keeping the 15 most recent images.

---

## 4. Deployment Instructions

### Prerequisites
- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (>= 1.5.0)
- AWS CLI configured with appropriate administrator credentials

### Deploying to Staging or Production
```bash
cd infrastructure/terraform/environments/staging

# 1. Initialize Terraform
terraform init

# 2. Review Execution Plan
terraform plan

# 3. Apply Infrastructure
terraform apply
```
