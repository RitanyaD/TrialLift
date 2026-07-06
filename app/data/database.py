import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.core.config import DB_PATH


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    segment TEXT NOT NULL,
    industry TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    acquisition_channel TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    monthly_price INTEGER NOT NULL,
    seat_limit INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    trial_start TEXT NOT NULL,
    trial_end TEXT NOT NULL,
    converted_at TEXT,
    cancelled_at TEXT,
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS feature_usage (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    feature_name TEXT NOT NULL,
    usage_count INTEGER NOT NULL,
    active_days INTEGER NOT NULL,
    last_used_at TEXT NOT NULL,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    target_segment TEXT NOT NULL,
    status TEXT NOT NULL,
    metric TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    intent TEXT NOT NULL,
    selected_agent TEXT NOT NULL,
    token_estimate INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_SQL)
    connection.commit()


def fetch_all(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    return [dict(row) for row in cursor.fetchall()]


def execute_write(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> None:
    connection.execute(sql, tuple(params))
    connection.commit()
