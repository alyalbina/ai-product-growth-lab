"""Portable SQLite export and query execution; no service is required."""

import sqlite3
from pathlib import Path

import pandas as pd


def create_database(tables, path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with sqlite3.connect(path) as connection:
        for name, frame in tables.items():
            if isinstance(frame, pd.DataFrame):
                frame.to_sql(name, connection, if_exists="replace", index=False)
        for table in ("user_days", "events", "ai_requests", "payments", "token_transactions"):
            if table in tables and "user_id" in tables[table].columns:
                connection.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_user ON "{table}"(user_id)')
        if "user_days" in tables:
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_days_age ON user_days(user_id, age_day)")
    return path


def run_queries(database_path, sql_root):
    results = {}
    with sqlite3.connect(Path(database_path).resolve()) as connection:
        for path in sorted(Path(sql_root).rglob("*.sql")):
            results[str(path.relative_to(sql_root)).replace("\\", "/")] = pd.read_sql_query(path.read_text(encoding="utf-8"), connection)
    return results
