# Zip the Lambda source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/src"
  output_path = "${path.module}/../lambda/collector.zip"
}

# Lambda function
resource "aws_lambda_function" "collector" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-collector"
  role             = aws_iam_role.lambda_role.arn
  handler          = "collector.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      APP_REGION   = var.aws_region
      PROJECT_NAME = var.project_name
      DB_PATH      = "/tmp/finops.db"
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch log group for Lambda
resource "aws_cloudwatch_log_group" "collector_logs" {
  name              = "/aws/lambda/${aws_lambda_function.collector.function_name}"
  retention_in_days = 14
}
