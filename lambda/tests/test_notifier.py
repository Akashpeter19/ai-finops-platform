import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Fresh SQLite DB for every test."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    import importlib
    import db
    importlib.reload(db)
    db.init_db()
    yield
    monkeypatch.delenv("DB_PATH", raising=False)


def make_sample_anomaly():
    return {
        "id": 1,
        "date": "2025-08-12",
        "service": "Amazon EC2",
        "actual_cost": 95.0,
        "expected_cost": 10.5,
        "z_score": 8.5,
        "severity": "HIGH",
        "rca_summary": "Autoscaling event caused spike.",
        "remediation": "Review scaling policies.",
        "alert_sent": 0
    }


def test_build_slack_message_contains_service():
    import importlib
    import notifier
    importlib.reload(notifier)
    message = notifier.build_slack_message(make_sample_anomaly())
    assert "Amazon EC2" in json.dumps(message, ensure_ascii=False)


def test_build_slack_message_contains_cost():
    import importlib
    import notifier
    importlib.reload(notifier)
    message = notifier.build_slack_message(make_sample_anomaly())
    assert "95.00" in json.dumps(message, ensure_ascii=False)


def test_build_slack_message_contains_rca():
    import importlib
    import notifier
    importlib.reload(notifier)
    message = notifier.build_slack_message(make_sample_anomaly())
    assert "Autoscaling event caused spike." in json.dumps(message, ensure_ascii=False)


def test_build_slack_message_high_severity_has_red_emoji():
    import importlib
    import notifier
    importlib.reload(notifier)
    message = notifier.build_slack_message(make_sample_anomaly())
    assert "🔴" in json.dumps(message, ensure_ascii=False)


def test_send_slack_alert_success():
    import importlib
    import notifier
    importlib.reload(notifier)
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = notifier.send_slack_alert(
            "https://hooks.slack.com/fake", {"text": "test"}
        )
    assert result is True


def test_send_slack_alert_failure():
    import importlib
    import notifier
    importlib.reload(notifier)
    import urllib.error
    with patch("urllib.request.urlopen",
               side_effect=urllib.error.URLError("timeout")):
        result = notifier.send_slack_alert(
            "https://hooks.slack.com/fake", {"text": "test"}
        )
    assert result is False


def test_run_notifications_skips_placeholder_webhook():
    import importlib
    import notifier
    importlib.reload(notifier)
    from db import insert_cost_data, insert_anomaly_event
    insert_cost_data("2025-08-12", "Amazon EC2", 95.0)
    insert_anomaly_event("2025-08-12", "Amazon EC2", 95.0, 10.5, 8.5, "HIGH")
    with patch("notifier.get_webhook_url", return_value="PLACEHOLDER"):
        sent = notifier.run_notifications()
    assert sent == 0
