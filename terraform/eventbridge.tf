# EventBridge rule — runs Lambda every day at 8am UTC
resource "aws_cloudwatch_event_rule" "daily_collector" {
  name                = "${var.project_name}-daily-collector"
  description         = "Triggers the FinOps collector Lambda daily"
  schedule_expression = "cron(0 8 * * ? *)"
}

# Connect the rule to the Lambda function
resource "aws_cloudwatch_event_target" "collector_target" {
  rule      = aws_cloudwatch_event_rule.daily_collector.name
  target_id = "CollectorLambda"
  arn       = aws_lambda_function.collector.arn
}

# Allow EventBridge to invoke the Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_collector.arn
}
