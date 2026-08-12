# ── Collector schedule — runs at 8am UTC daily ────────────────
resource "aws_cloudwatch_event_rule" "daily_collector" {
  name                = "${var.project_name}-daily-collector"
  description         = "Triggers the FinOps collector Lambda daily"
  schedule_expression = "cron(0 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "collector_target" {
  rule      = aws_cloudwatch_event_rule.daily_collector.name
  target_id = "CollectorLambda"
  arn       = aws_lambda_function.collector.arn
}

resource "aws_lambda_permission" "allow_eventbridge_collector" {
  statement_id  = "AllowEventBridgeInvokeCollector"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_collector.arn
}

# ── Anomaly detector — runs at 8:10am UTC daily ───────────────
# Runs 10 minutes after collector so data is ready
resource "aws_cloudwatch_event_rule" "daily_anomaly" {
  name                = "${var.project_name}-daily-anomaly"
  description         = "Triggers the anomaly detector Lambda daily"
  schedule_expression = "cron(10 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "anomaly_target" {
  rule      = aws_cloudwatch_event_rule.daily_anomaly.name
  target_id = "AnomalyDetectorLambda"
  arn       = aws_lambda_function.anomaly_detector.arn
}

resource "aws_lambda_permission" "allow_eventbridge_anomaly" {
  statement_id  = "AllowEventBridgeInvokeAnomaly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.anomaly_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_anomaly.arn
}
