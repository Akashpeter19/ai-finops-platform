import logging
import statistics
from db import (
    init_db,
    get_all_services,
    get_cost_last_n_days,
    insert_anomaly_event
)

logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# How many days of history to use for baseline
LOOKBACK_DAYS = 8

# How many standard deviations above mean = anomaly
Z_SCORE_THRESHOLD = 2.0

# Minimum spend to bother alerting on (avoids noise on $0.01 spikes)
MIN_COST_THRESHOLD = 1.0


def calculate_moving_average(amounts):
    """Calculate mean of a list of amounts."""
    if not amounts:
        return 0.0
    return sum(amounts) / len(amounts)


def calculate_z_score(value, mean, stddev):
    """
    Calculate how many standard deviations value is from mean.
    Returns 0 if stddev is 0 (no variation in data).
    """
    if stddev == 0:
        return 0.0
    return (value - mean) / stddev


def determine_severity(z_score):
    """
    Map z-score to severity level.
    LOW < 2, MEDIUM 2-3, HIGH > 3
    """
    if z_score >= 3.0:
        return "HIGH"
    elif z_score >= 2.0:
        return "MEDIUM"
    else:
        return "LOW"


def detect_anomalies_for_service(service):
    """
    Check if the most recent day's cost for a service is anomalous.
    Uses last LOOKBACK_DAYS days as baseline.
    Returns anomaly dict or None.
    """
    # Get last N days — index 0 is most recent
    rows = get_cost_last_n_days(service, n=LOOKBACK_DAYS)

    # Need at least 3 days of history to detect anomalies
    if len(rows) < 3:
        logger.info(f"Not enough history for {service} — skipping")
        return None

    # Most recent day is what we're checking
    latest = rows[0]
    actual_cost = latest["amount"]
    latest_date = latest["date"]

    # Skip tiny costs — not worth alerting
    if actual_cost < MIN_COST_THRESHOLD:
        return None

    # Baseline = all days EXCEPT the most recent
    baseline_amounts = [row["amount"] for row in rows[1:]]

    mean = calculate_moving_average(baseline_amounts)

    # Need at least 2 points for stddev
    if len(baseline_amounts) < 2:
        return None

    stddev = statistics.stdev(baseline_amounts)
    z_score = calculate_z_score(actual_cost, mean, stddev)

    logger.info(
        f"{service} | date={latest_date} | actual={actual_cost:.2f} "
        f"| mean={mean:.2f} | stddev={stddev:.2f} | z={z_score:.2f}"
    )

    # Flag as anomaly if z-score exceeds threshold
    if z_score >= Z_SCORE_THRESHOLD:
        severity = determine_severity(z_score)
        logger.info(f"ANOMALY DETECTED: {service} | severity={severity}")
        return {
            "date": latest_date,
            "service": service,
            "actual_cost": actual_cost,
            "expected_cost": round(mean, 4),
            "z_score": round(z_score, 4),
            "severity": severity
        }

    return None


def run_anomaly_detection():
    """
    Run anomaly detection across all services.
    Returns list of detected anomalies.
    """
    logger.info("Starting anomaly detection run")

    services = get_all_services()
    logger.info(f"Checking {len(services)} services")

    anomalies = []
    for service in services:
        result = detect_anomalies_for_service(service)
        if result:
            event_id = insert_anomaly_event(
                date=result["date"],
                service=result["service"],
                actual_cost=result["actual_cost"],
                expected_cost=result["expected_cost"],
                z_score=result["z_score"],
                severity=result["severity"]
            )
            result["event_id"] = event_id
            anomalies.append(result)

    logger.info(f"Anomaly detection complete — found {len(anomalies)} anomalies")
    return anomalies


def lambda_handler(event, context):
    """
    Lambda entry point for anomaly detection.
    Can be chained after collector or run separately.
    """
    logger.info("Anomaly detector Lambda started")

    init_db()

    anomalies = run_anomaly_detection()

    return {
        "statusCode": 200,
        "body": f"Detected {len(anomalies)} anomalies",
        "anomalies": anomalies
    }
