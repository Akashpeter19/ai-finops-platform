import boto3
import logging
import os
from datetime import datetime, timedelta
from db import init_db, insert_cost_data

# Structured logging
logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Use APP_REGION instead of AWS_REGION (reserved by Lambda)
APP_REGION = os.environ.get("APP_REGION", "us-east-1")


def get_cost_explorer_client():
    """Return a Cost Explorer boto3 client."""
    return boto3.client("ce", region_name=APP_REGION)


def fetch_daily_costs(start_date, end_date):
    """
    Fetch daily costs per AWS service from Cost Explorer.
    Returns list of dicts: {date, service, amount, currency}
    """
    client = get_cost_explorer_client()
    logger.info(f"Fetching costs from {start_date} to {end_date}")

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date,
            "End": end_date
        },
        Granularity="DAILY",
        Metrics=["BlendedCost"],
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE"
            }
        ]
    )

    results = []
    for day in response.get("ResultsByTime", []):
        date = day["TimePeriod"]["Start"]
        for group in day.get("Groups", []):
            service = group["Keys"][0]
            amount = float(group["Metrics"]["BlendedCost"]["Amount"])
            currency = group["Metrics"]["BlendedCost"]["Unit"]

            if amount > 0:
                results.append({
                    "date": date,
                    "service": service,
                    "amount": amount,
                    "currency": currency
                })

    logger.info(f"Fetched {len(results)} cost records")
    return results


def lambda_handler(event, context):
    """
    Main Lambda entry point.
    Triggered daily by EventBridge.
    Fetches last 30 days of costs and stores in SQLite.
    """
    logger.info("Collector Lambda started")

    init_db()

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=30)

    costs = fetch_daily_costs(
        start_date=str(start_date),
        end_date=str(end_date)
    )

    stored = 0
    for record in costs:
        insert_cost_data(
            date=record["date"],
            service=record["service"],
            amount=record["amount"],
            currency=record["currency"]
        )
        stored += 1

    logger.info(f"Collector complete — stored {stored} records")

    return {
        "statusCode": 200,
        "body": f"Stored {stored} cost records"
    }
