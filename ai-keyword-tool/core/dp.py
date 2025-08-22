import sqlite3
import uuid
from datetime import datetime

DB_NAME = "app_data.db"

def connect_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    with connect_db() as conn:
        # Create sessions table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            topic TEXT
        );
        """)
        # Create briefs table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS briefs (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            content TEXT,
            created_at TEXT
        );
        """)
        print("Database initialized.")

def save_session(topic):
    session_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    with connect_db() as conn:
        conn.execute("INSERT INTO sessions (id, created_at, topic) VALUES (?, ?, ?)",
                     (session_id, created_at, topic))
    return session_id

def save_brief(session_id, content):
    brief_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    with connect_db() as conn:
        conn.execute("INSERT INTO briefs (id, session_id, content, created_at) VALUES (?, ?, ?, ?)",
                     (brief_id, session_id, content, created_at))
