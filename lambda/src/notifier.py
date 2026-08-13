import boto3
import json
import logging
import os
import urllib.request
import urllib.error
from db import get_unalerted_anomalies, mark_alert_sent, init_db

logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

APP_REGION = os.environ.get("APP_REGION", "us-east-1")
SSM_WEBHOOK_KEY = "/finops/slack_webhook_url"


def get_webhook_url():
    """Fetch Slack webhook URL from SSM Parameter Store."""
    client = boto3.client("ssm", region_name=APP_REGION)
    response = client.get_parameter(
        Name=SSM_WEBHOOK_KEY,
        WithDecryption=True
    )
    return response["Parameter"]["Value"]


def build_slack_message(anomaly):
    """Build a Slack Block Kit message for an anomaly."""
    severity_emoji = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }.get(anomaly.get("severity", "MEDIUM"), "🟡")

    cost_increase = anomaly["actual_cost"] - anomaly["expected_cost"]
    pct_increase = ((anomaly["actual_cost"] / anomaly["expected_cost"]) - 1) * 100
    rca_text = anomaly.get("rca_summary") or "RCA pending — check CloudWatch logs."
    remediation_text = anomaly.get("remediation") or "Review AWS Cost Explorer for details."

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji} AWS Cost Anomaly Detected"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Service:*\n{anomaly['service']}"},
                {"type": "mrkdwn", "text": f"*Date:*\n{anomaly['date']}"},
                {"type": "mrkdwn", "text": f"*Actual Cost:*\n${anomaly['actual_cost']:.2f}"},
                {"type": "mrkdwn", "text": f"*Expected Cost:*\n${anomaly['expected_cost']:.2f}"},
                {"type": "mrkdwn",
                 "text": f"*Increase:*\n${cost_increase:.2f} ({pct_increase:.0f}% above normal)"},
                {"type": "mrkdwn", "text": f"*Severity:*\n{severity_emoji} {anomaly['severity']}"}
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*AI Root Cause Analysis:*\n{rca_text}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recommended Actions:*\n{remediation_text}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Z-Score: {anomaly.get('z_score', 'N/A')} | AI FinOps Platform"
                }
            ]
        }
    ]
    return {"blocks": blocks}


def send_slack_alert(webhook_url, message):
    """Send message to Slack via webhook."""
    payload = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.info("Slack alert sent successfully")
                return True
            else:
                logger.error(f"Slack returned status {response.status}")
                return False
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


def run_notifications():
    """Fetch unalerted anomalies and send Slack alerts for each."""
    anomalies = get_unalerted_anomalies()
    logger.info(f"Found {len(anomalies)} unalerted anomalies")

    if not anomalies:
        return 0

    webhook_url = get_webhook_url()

    if webhook_url == "PLACEHOLDER":
        logger.warning("Slack webhook is PLACEHOLDER — skipping alerts")
        return 0

    sent = 0
    for anomaly in anomalies:
        message = build_slack_message(anomaly)
        success = send_slack_alert(webhook_url, message)
        if success:
            mark_alert_sent(anomaly["id"])
            sent += 1
            logger.info(f"Alert sent for {anomaly['service']} on {anomaly['date']}")
        else:
            logger.error(f"Failed to send alert for {anomaly['service']}")
    return sent


def lambda_handler(event, context):
    """Lambda entry point for Slack notifications."""
    logger.info("Notifier Lambda started")
    init_db()
    sent = run_notifications()
    return {
        "statusCode": 200,
        "body": f"Sent {sent} Slack alerts"
    }
