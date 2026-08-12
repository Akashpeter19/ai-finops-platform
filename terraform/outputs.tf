output "collector_function_name" {
  description = "Collector Lambda function name"
  value       = aws_lambda_function.collector.function_name
}

output "anomaly_detector_function_name" {
  description = "Anomaly detector Lambda function name"
  value       = aws_lambda_function.anomaly_detector.function_name
}

output "collector_function_arn" {
  description = "Collector Lambda ARN"
  value       = aws_lambda_function.collector.arn
}

output "anomaly_detector_function_arn" {
  description = "Anomaly detector Lambda ARN"
  value       = aws_lambda_function.anomaly_detector.arn
}
