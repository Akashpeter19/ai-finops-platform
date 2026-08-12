# Zip the Lambda source code (shared by both functions)
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/src"
  output_path = "${path.module}/../lambda/collector.zip"
}

# ── Collector Lambda ──────────────────────────────────────────
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

resource "aws_cloudwatch_log_group" "collector_logs" {
  name              = "/aws/lambda/${aws_lambda_function.collector.function_name}"
  retention_in_days = 14
}

# ── Anomaly Detector Lambda ───────────────────────────────────
resource "aws_lambda_function" "anomaly_detector" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-anomaly-detector"
  role             = aws_iam_role.lambda_role.arn
  handler          = "anomaly.lambda_handler"
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

resource "aws_cloudwatch_log_group" "anomaly_logs" {
  name              = "/aws/lambda/${aws_lambda_function.anomaly_detector.function_name}"
  retention_in_days = 14
}

# ── RCA Lambda ────────────────────────────────────────────────
resource "aws_lambda_function" "rca" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-rca"
  role             = aws_iam_role.lambda_role.arn
  handler          = "rca.lambda_handler"
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

resource "aws_cloudwatch_log_group" "rca_logs" {
  name              = "/aws/lambda/${aws_lambda_function.rca.function_name}"
  retention_in_days = 14
}
