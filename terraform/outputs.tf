output "collector_function_name" {
  value = aws_lambda_function.collector.function_name
}

output "anomaly_detector_function_name" {
  value = aws_lambda_function.anomaly_detector.function_name
}

output "rca_function_name" {
  value = aws_lambda_function.rca.function_name
}

output "collector_function_arn" {
  value = aws_lambda_function.collector.arn
}

output "anomaly_detector_function_arn" {
  value = aws_lambda_function.anomaly_detector.arn
}

output "rca_function_arn" {
  value = aws_lambda_function.rca.arn
}
