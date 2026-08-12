output "lambda_function_name" {
  description = "Name of the collector Lambda function"
  value       = aws_lambda_function.collector.function_name
}

output "lambda_function_arn" {
  description = "ARN of the collector Lambda function"
  value       = aws_lambda_function.collector.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge daily schedule rule"
  value       = aws_cloudwatch_event_rule.daily_collector.name
}
