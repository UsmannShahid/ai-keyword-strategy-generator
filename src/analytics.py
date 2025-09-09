# src/analytics.py
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
import sqlite3
import json
from datetime import datetime

DB_PATH = "app_data.db"

def init_analytics_db():
    """Initialize the analytics database tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        plan TEXT,
        event_type TEXT,
        endpoint TEXT,
        keyword TEXT,
        latency_ms INTEGER,
        success BOOLEAN,
        error TEXT,
        meta_json TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def log_event(
    user_id: str,
    plan: str = "free",
    event_type: str = "api_call",
    endpoint: str = "",
    keyword: str = "",
    latency_ms: int = 0,
    success: bool = True,
    error: Optional[str] = None,
    meta_json: Optional[str] = None
):
    """Log an analytics event to the database."""
    try:
        init_analytics_db()  # Ensure table exists
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO events (user_id, plan, event_type, endpoint, keyword, latency_ms, success, error, meta_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, plan, event_type, endpoint, keyword, latency_ms, success, error, meta_json))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Failed to log analytics event: {e}")

@contextmanager
def timed(operation_name: str = "operation"):
    """Context manager to time operations."""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        print(f"DEBUG: {operation_name} took {elapsed_ms}ms")

class TimedContext:
    """A context manager that tracks elapsed time."""
    
    def __init__(self):
        self.start_time = None
        self.elapsed_ms = 0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.elapsed_ms = int((time.time() - self.start_time) * 1000)

def get_summary() -> Dict[str, Any]:
    """Get analytics summary."""
    try:
        init_analytics_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE success = 1")
        successful_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(latency_ms) FROM events WHERE latency_ms > 0")
        avg_latency = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_events": total_events,
            "successful_events": successful_events,
            "average_latency_ms": round(avg_latency, 2),
            "success_rate": round((successful_events / total_events * 100) if total_events > 0 else 0, 2)
        }
    except Exception as e:
        print(f"Error getting summary: {e}")
        return {"total_events": 0, "successful_events": 0, "average_latency_ms": 0, "success_rate": 0}

def get_top_users(limit: int = 10) -> list:
    """Get top users by activity."""
    try:
        init_analytics_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT user_id, COUNT(*) as event_count
        FROM events
        GROUP BY user_id
        ORDER BY event_count DESC
        LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{"user_id": row[0], "event_count": row[1]} for row in results]
    except Exception as e:
        print(f"Error getting top users: {e}")
        return []

def get_funnel() -> Dict[str, Any]:
    """Get funnel analytics."""
    try:
        init_analytics_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT endpoint, COUNT(*) FROM events GROUP BY endpoint")
        endpoint_counts = cursor.fetchall()
        
        cursor.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
        event_type_counts = cursor.fetchall()
        
        conn.close()
        
        return {
            "endpoints": [{"endpoint": row[0], "count": row[1]} for row in endpoint_counts],
            "event_types": [{"event_type": row[0], "count": row[1]} for row in event_type_counts]
        }
    except Exception as e:
        print(f"Error getting funnel: {e}")
        return {"endpoints": [], "event_types": []}
