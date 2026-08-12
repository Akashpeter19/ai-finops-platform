import pytest
import sys
import os
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Give every test its own fresh SQLite file."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)

    # Import AFTER env var is set so db.py picks up the right path
    import importlib
    import db
    importlib.reload(db)
    db.init_db()
    yield
    monkeypatch.delenv("DB_PATH", raising=False)


def test_init_db_creates_tables():
    """init_db should create cost_data and anomaly_events tables."""
    import db
    conn = sqlite3.connect(os.environ["DB_PATH"])
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "cost_data" in tables
    assert "anomaly_events" in tables


def test_insert_cost_data_stores_record():
    """insert_cost_data should store one record for one service+date."""
    from db import insert_cost_data, get_cost_last_n_days
    insert_cost_data("2025-01-15", "Amazon EC2", 12.50)
    rows = get_cost_last_n_days("Amazon EC2", n=7)
    assert len(rows) == 1
    assert rows[0]["date"] == "2025-01-15"
    assert rows[0]["amount"] == 12.50


def test_insert_cost_data_upserts_on_duplicate():
    """Inserting same date+service twice should update, not duplicate."""
    from db import insert_cost_data, get_cost_last_n_days
    insert_cost_data("2025-01-15", "Amazon S3", 5.00)
    insert_cost_data("2025-01-15", "Amazon S3", 9.99)
    rows = get_cost_last_n_days("Amazon S3", n=7)
    assert len(rows) == 1
    assert rows[0]["amount"] == 9.99


def test_get_all_services_returns_unique_services():
    """get_all_services should return unique service names."""
    from db import insert_cost_data, get_all_services
    insert_cost_data("2025-01-14", "Amazon EC2", 10.00)
    insert_cost_data("2025-01-15", "Amazon EC2", 11.00)
    insert_cost_data("2025-01-15", "Amazon S3", 2.00)
    services = get_all_services()
    assert "Amazon EC2" in services
    assert "Amazon S3" in services
    assert len(services) == 2


def test_get_cost_last_n_days_limits_results():
    """get_cost_last_n_days should return at most n records."""
    from db import insert_cost_data, get_cost_last_n_days
    for i in range(10):
        insert_cost_data(f"2025-01-{i+1:02d}", "Amazon EC2", float(i))
    rows = get_cost_last_n_days("Amazon EC2", n=3)
    assert len(rows) == 3
