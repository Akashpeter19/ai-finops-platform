import pytest
import sys
import os

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


def test_calculate_moving_average_normal():
    """Moving average of known values should be correct."""
    from anomaly import calculate_moving_average
    result = calculate_moving_average([10.0, 20.0, 30.0])
    assert result == 20.0


def test_calculate_moving_average_empty():
    """Empty list should return 0."""
    from anomaly import calculate_moving_average
    assert calculate_moving_average([]) == 0.0


def test_calculate_z_score_normal():
    """Z-score should correctly measure deviation."""
    from anomaly import calculate_z_score
    # value=30, mean=20, stddev=5 → z=2.0
    result = calculate_z_score(30.0, 20.0, 5.0)
    assert result == 2.0


def test_calculate_z_score_zero_stddev():
    """Z-score with zero stddev should return 0 not divide by zero."""
    from anomaly import calculate_z_score
    result = calculate_z_score(100.0, 100.0, 0.0)
    assert result == 0.0


def test_determine_severity_high():
    """Z-score >= 3 should be HIGH."""
    from anomaly import determine_severity
    assert determine_severity(3.5) == "HIGH"


def test_determine_severity_medium():
    """Z-score between 2 and 3 should be MEDIUM."""
    from anomaly import determine_severity
    assert determine_severity(2.5) == "MEDIUM"


def test_determine_severity_low():
    """Z-score below 2 should be LOW."""
    from anomaly import determine_severity
    assert determine_severity(1.5) == "LOW"


def test_detect_anomaly_flags_spike():
    """A day with cost 3x the baseline mean should be flagged."""
    from db import insert_cost_data
    import importlib
    import anomaly
    importlib.reload(anomaly)

    # Insert 7 days of normal baseline costs for EC2
    normal_days = [
        ("2025-01-01", 10.0),
        ("2025-01-02", 11.0),
        ("2025-01-03", 10.5),
        ("2025-01-04", 10.0),
        ("2025-01-05", 11.5),
        ("2025-01-06", 10.0),
    ]
    for date, amount in normal_days:
        insert_cost_data(date, "Amazon EC2", amount)

    # Insert a spike day as the most recent
    insert_cost_data("2025-01-07", "Amazon EC2", 95.0)

    result = anomaly.detect_anomalies_for_service("Amazon EC2")
    assert result is not None
    assert result["service"] == "Amazon EC2"
    assert result["severity"] in ("MEDIUM", "HIGH")
    assert result["actual_cost"] == 95.0


def test_detect_anomaly_no_flag_for_normal_spend():
    """Normal spend variation should not trigger an anomaly."""
    from db import insert_cost_data
    import importlib
    import anomaly
    importlib.reload(anomaly)

    # Insert consistent costs — no spike
    days = [
        ("2025-01-01", 10.0),
        ("2025-01-02", 10.5),
        ("2025-01-03", 10.2),
        ("2025-01-04", 10.8),
        ("2025-01-05", 10.1),
        ("2025-01-06", 10.3),
        ("2025-01-07", 10.4),
    ]
    for date, amount in days:
        insert_cost_data(date, "Amazon EC2", amount)

    result = anomaly.detect_anomalies_for_service("Amazon EC2")
    assert result is None


def test_run_anomaly_detection_returns_list():
    """run_anomaly_detection should always return a list."""
    import importlib
    import anomaly
    importlib.reload(anomaly)
    result = anomaly.run_anomaly_detection()
    assert isinstance(result, list)
