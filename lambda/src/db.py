import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Database path — Lambda uses /tmp for writable storage
DB_PATH = os.environ.get("DB_PATH", "/tmp/finops.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Table 1: stores daily cost per AWS service
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_data (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                service     TEXT NOT NULL,
                amount      REAL NOT NULL,
                currency    TEXT DEFAULT 'USD',
                created_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(date, service)
            )
        """)

        # Table 2: stores detected anomaly events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                date          TEXT NOT NULL,
                service       TEXT NOT NULL,
                actual_cost   REAL NOT NULL,
                expected_cost REAL NOT NULL,
                z_score       REAL,
                severity      TEXT DEFAULT 'MEDIUM',
                rca_summary   TEXT,
                remediation   TEXT,
                alert_sent    INTEGER DEFAULT 0,
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)

        conn.commit()
        logger.info("Database initialised successfully")
    finally:
        conn.close()


def insert_cost_data(date, service, amount, currency="USD"):
    """Insert or update a daily cost record."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cost_data (date, service, amount, currency)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date, service) DO UPDATE SET
                amount = excluded.amount
        """, (date, service, amount, currency))
        conn.commit()
        logger.info(f"Stored cost: {date} | {service} | {amount} {currency}")
    finally:
        conn.close()


def get_cost_last_n_days(service, n=7):
    """Get the last N days of cost data for a service."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, amount
            FROM cost_data
            WHERE service = ?
            ORDER BY date DESC
            LIMIT ?
        """, (service, n))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_services():
    """Get list of all unique services in cost_data."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT service FROM cost_data
            ORDER BY service
        """)
        rows = cursor.fetchall()
        return [row["service"] for row in rows]
    finally:
        conn.close()


def insert_anomaly_event(date, service, actual_cost,
                         expected_cost, z_score, severity):
    """Insert a new anomaly event."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO anomaly_events
                (date, service, actual_cost, expected_cost, z_score, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date, service, actual_cost, expected_cost, z_score, severity))
        conn.commit()
        event_id = cursor.lastrowid
        logger.info(f"Anomaly recorded: {service} on {date} | severity={severity}")
        return event_id
    finally:
        conn.close()


def get_unalerted_anomalies():
    """Get anomaly events that have not been sent to Slack yet."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM anomaly_events
            WHERE alert_sent = 0
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_alert_sent(event_id):
    """Mark an anomaly event as alerted."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE anomaly_events SET alert_sent = 1 WHERE id = ?
        """, (event_id,))
        conn.commit()
    finally:
        conn.close()
