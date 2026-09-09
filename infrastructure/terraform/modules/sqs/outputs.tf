output "queue_arns" {
  description = "Map of agent queue names to their ARNs"
  value       = { for k, v in aws_sqs_queue.queues : k => v.arn }
}

output "queue_urls" {
  description = "Map of agent queue names to their URLs"
  value       = { for k, v in aws_sqs_queue.queues : k => v.id }
}

output "dlq_arns" {
  description = "Map of agent DLQ names to their ARNs"
  value       = { for k, v in aws_sqs_queue.dlqs : k => v.arn }
}

output "dlq_urls" {
  description = "Map of agent DLQ names to their URLs"
  value       = { for k, v in aws_sqs_queue.dlqs : k => v.id }
}
