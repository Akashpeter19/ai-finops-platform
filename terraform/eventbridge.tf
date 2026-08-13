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

# ── RCA Lambda — runs at 8:20am UTC daily ────────────────────
# Runs 10 minutes after anomaly detector
resource "aws_cloudwatch_event_rule" "daily_rca" {
  name                = "${var.project_name}-daily-rca"
  description         = "Triggers the RCA Lambda daily"
  schedule_expression = "cron(20 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "rca_target" {
  rule      = aws_cloudwatch_event_rule.daily_rca.name
  target_id = "RCALambda"
  arn       = aws_lambda_function.rca.arn
}

resource "aws_lambda_permission" "allow_eventbridge_rca" {
  statement_id  = "AllowEventBridgeInvokeRCA"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rca.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_rca.arn
}

# ── Notifier Lambda — runs at 8:30am UTC daily ───────────────
resource "aws_cloudwatch_event_rule" "daily_notifier" {
  name                = "${var.project_name}-daily-notifier"
  description         = "Triggers the notifier Lambda daily"
  schedule_expression = "cron(30 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "notifier_target" {
  rule      = aws_cloudwatch_event_rule.daily_notifier.name
  target_id = "NotifierLambda"
  arn       = aws_lambda_function.notifier.arn
}

resource "aws_lambda_permission" "allow_eventbridge_notifier" {
  statement_id  = "AllowEventBridgeInvokeNotifier"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_notifier.arn
}
