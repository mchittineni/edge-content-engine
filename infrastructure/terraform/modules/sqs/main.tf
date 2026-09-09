# Decoupled SQS Architecture with SSE Encryption, Dead-Letter Queues (DLQ), and CloudWatch Alarms

locals {
  agent_queues = [
    "edge-discovery",
    "edge-scoring",
    "edge-research",
    "edge-writing",
    "edge-architecture",
    "edge-validation",
    "edge-seo",
    "edge-approval",
    "edge-publishing",
    "edge-social",
    "edge-analytics"
  ]
}

# 1. Dead-Letter Queues (DLQs)
resource "aws_sqs_queue" "dlqs" {
  for_each                  = toset(local.agent_queues)
  name                      = "${each.key}-dlq-${var.environment}"
  message_retention_seconds = var.dlq_message_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = {
    Name        = "${each.key}-dlq-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
    Type        = "DLQ"
  }
}

# 2. Main Agent Processing Queues
resource "aws_sqs_queue" "queues" {
  for_each                   = toset(local.agent_queues)
  name                       = "${each.key}-${var.environment}"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlqs[each.key].arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = {
    Name        = "${each.key}-${var.environment}"
    Project     = "EDGE"
    Environment = var.environment
    Type        = "AgentQueue"
  }
}

# 3. DLQ Redrive Allow Policy (Restricting dead-letter ingestion exclusively to the paired queue)
resource "aws_sqs_queue_redrive_allow_policy" "dlq_allow_policy" {
  for_each  = toset(local.agent_queues)
  queue_url = aws_sqs_queue.dlqs[each.key].id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.queues[each.key].arn]
  })
}

# 4. CloudWatch Metric Alarms for DLQs
resource "aws_cloudwatch_metric_alarm" "dlq_alarm" {
  for_each            = toset(local.agent_queues)
  alarm_name          = "${each.key}-dlq-alarm-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Alarm triggered when unhandled failed messages land in ${each.key} DLQ"

  dimensions = {
    QueueName = aws_sqs_queue.dlqs[each.key].name
  }

  alarm_actions = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  tags = {
    Project     = "EDGE"
    Environment = var.environment
  }
}
