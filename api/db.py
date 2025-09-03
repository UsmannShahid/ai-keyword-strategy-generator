import sqlite3
from pathlib import Path
from datetime import datetime

# SQLite DB path (reuses existing app_data.db at project root)
DB_PATH = Path("app_data.db")


def get_conn():
    """Return a new SQLite connection to the app DB."""
    return sqlite3.connect(DB_PATH)


def init_usage_tables():
    """Create usage-related tables if they do not already exist."""
    with get_conn() as conn:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          email TEXT,
          plan TEXT DEFAULT 'free'
        );
        """
        )
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS usage_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT,
          action TEXT,
          qty INTEGER,
          ts TEXT
        );
        """
        )
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS quotas (
          plan TEXT,
          action TEXT,
          monthly_limit INTEGER,
          PRIMARY KEY (plan, action)
        );
        """
        )

