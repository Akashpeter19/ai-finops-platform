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
    """Return a sample anomaly dict for testing."""
    return {
        "id": 1,
        "date": "2025-01-07",
        "service": "Amazon EC2",
        "actual_cost": 95.0,
        "expected_cost": 10.5,
        "z_score": 8.5,
        "severity": "HIGH",
        "alert_sent": 0
    }


def test_build_rca_prompt_contains_service():
    """RCA prompt should include the service name."""
    import importlib
    import rca
    importlib.reload(rca)
    anomaly = make_sample_anomaly()
    prompt = rca.build_rca_prompt(anomaly)
    assert "Amazon EC2" in prompt
    assert "95.00" in prompt
    assert "HIGH" in prompt


def test_build_rca_prompt_contains_cost_details():
    """RCA prompt should include actual and expected cost."""
    import importlib
    import rca
    importlib.reload(rca)
    anomaly = make_sample_anomaly()
    prompt = rca.build_rca_prompt(anomaly)
    assert "10.50" in prompt
    assert "2025-01-07" in prompt


def test_call_bedrock_returns_parsed_json():
    """call_bedrock should return parsed dict on success."""
    import importlib
    import rca
    importlib.reload(rca)

    mock_response = {
        "root_cause": "Sudden EC2 usage spike due to autoscaling event.",
        "remediation": "1. Check autoscaling logs. 2. Review scaling policies. 3. Set budget alerts.",
        "prevention": "Set tighter autoscaling limits and cost alerts."
    }

    # Mock the boto3 Bedrock client
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps({
        "content": [{"text": json.dumps(mock_response)}]
    })

    mock_client = MagicMock()
    mock_client.invoke_model.return_value = {"body": mock_body}

    with patch("rca.get_bedrock_client", return_value=mock_client):
        result = rca.call_bedrock("test prompt")

    assert result is not None
    assert result["root_cause"] == mock_response["root_cause"]
    assert result["remediation"] == mock_response["remediation"]


def test_call_bedrock_returns_none_on_failure():
    """call_bedrock should return None when Bedrock throws an exception."""
    import importlib
    import rca
    importlib.reload(rca)

    mock_client = MagicMock()
    mock_client.invoke_model.side_effect = Exception("Bedrock unavailable")

    with patch("rca.get_bedrock_client", return_value=mock_client):
        result = rca.call_bedrock("test prompt")

    assert result is None


def test_save_rca_to_db_updates_record():
    """save_rca_to_db should update rca_summary and remediation fields."""
    import importlib
    import db
    import rca
    importlib.reload(rca)

    from db import insert_cost_data, insert_anomaly_event
    insert_cost_data("2025-01-07", "Amazon EC2", 95.0)
    event_id = insert_anomaly_event(
        date="2025-01-07",
        service="Amazon EC2",
        actual_cost=95.0,
        expected_cost=10.5,
        z_score=8.5,
        severity="HIGH"
    )

    rca_data = {
        "root_cause": "Autoscaling event caused spike.",
        "remediation": "Review scaling policies.",
        "prevention": "Set tighter limits."
    }

    rca.save_rca_to_db(event_id, rca_data)

    import sqlite3
    conn = sqlite3.connect(os.environ["DB_PATH"])
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rca_summary, remediation FROM anomaly_events WHERE id = ?",
        (event_id,)
    )
    row = cursor.fetchone()
    conn.close()

    assert row[0] == "Autoscaling event caused spike."
    assert row[1] == "Review scaling policies."
