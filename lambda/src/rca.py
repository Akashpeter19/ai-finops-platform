import boto3
import json
import logging
import os
from db import get_unalerted_anomalies, get_connection, init_db

logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

APP_REGION = os.environ.get("APP_REGION", "us-east-1")
BEDROCK_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def get_bedrock_client():
    """Return a Bedrock runtime client."""
    return boto3.client("bedrock-runtime", region_name=APP_REGION)


def build_rca_prompt(anomaly):
    """
    Build a prompt for Bedrock to analyse a cost anomaly.
    """
    return f"""You are a senior AWS FinOps engineer.
Analyse this AWS cost anomaly and provide a root cause analysis.

ANOMALY DETAILS:
- AWS Service: {anomaly['service']}
- Date: {anomaly['date']}
- Actual Cost: ${anomaly['actual_cost']:.2f}
- Expected Cost (7-day average): ${anomaly['expected_cost']:.2f}
- Cost Increase: ${anomaly['actual_cost'] - anomaly['expected_cost']:.2f} \
({((anomaly['actual_cost'] / anomaly['expected_cost']) - 1) * 100:.0f}% above normal)
- Severity: {anomaly['severity']}
- Z-Score: {anomaly['z_score']}

Respond in this exact JSON format with no extra text:
{{
  "root_cause": "2-3 sentence explanation of the most likely cause of this cost spike",
  "remediation": "3 specific actionable steps to investigate and fix this issue",
  "prevention": "1-2 sentences on how to prevent this in future"
}}"""


def call_bedrock(prompt):
    """
    Call AWS Bedrock Claude model with the RCA prompt.
    Returns parsed JSON response or None on failure.
    """
    client = get_bedrock_client()

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())
        raw_text = response_body["content"][0]["text"]
        logger.info("Bedrock response received successfully")
        rca_data = json.loads(raw_text)
        return rca_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Bedrock JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"Bedrock call failed: {e}")
        return None


def save_rca_to_db(event_id, rca_data):
    """Save RCA results back to the anomaly_events table."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE anomaly_events
            SET rca_summary = ?,
                remediation = ?
            WHERE id = ?
        """, (
            rca_data.get("root_cause", ""),
            rca_data.get("remediation", ""),
            event_id
        ))
        conn.commit()
        logger.info(f"RCA saved for anomaly event {event_id}")
    finally:
        conn.close()


def run_rca_for_anomalies():
    """
    Fetch all unalerted anomalies and generate RCA for each.
    Returns list of enriched anomaly dicts.
    """
    anomalies = get_unalerted_anomalies()
    logger.info(f"Running RCA for {len(anomalies)} anomalies")

    enriched = []
    for anomaly in anomalies:
        logger.info(f"Generating RCA for {anomaly['service']} on {anomaly['date']}")

        prompt = build_rca_prompt(anomaly)
        rca_data = call_bedrock(prompt)

        if rca_data:
            save_rca_to_db(anomaly["id"], rca_data)
            anomaly["rca_summary"] = rca_data.get("root_cause", "")
            anomaly["remediation"] = rca_data.get("remediation", "")
            anomaly["prevention"] = rca_data.get("prevention", "")
            enriched.append(anomaly)
            logger.info(f"RCA complete for {anomaly['service']}")
        else:
            logger.warning(f"RCA failed for {anomaly['service']} — skipping")

    return enriched


def lambda_handler(event, context):
    """
    Lambda entry point for RCA generation.
    Runs after anomaly detector.
    """
    logger.info("RCA Lambda started")

    # CRITICAL — initialise DB tables before querying
    init_db()

    enriched = run_rca_for_anomalies()

    return {
        "statusCode": 200,
        "body": f"Generated RCA for {len(enriched)} anomalies",
        "anomalies": enriched
    }
