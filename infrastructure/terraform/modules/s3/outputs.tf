output "bucket_name" {
  description = "Name of the S3 content lake bucket"
  value       = aws_s3_bucket.content_lake.id
}

output "bucket_arn" {
  description = "ARN of the S3 content lake bucket"
  value       = aws_s3_bucket.content_lake.arn
}
