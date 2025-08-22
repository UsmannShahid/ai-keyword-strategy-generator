import sqlite3
import uuid
import json
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

def extend_db():
    """Extend database with suggestions and serps tables."""
    with connect_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            variant TEXT,
            content TEXT,
            created_at TEXT
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS serps (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            data TEXT,
            created_at TEXT
        );
        """)
        print("Tables extended.")

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

def get_recent_sessions(limit=5):
    with connect_db() as conn:
        rows = conn.execute("SELECT id, topic, created_at FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
        return rows.fetchall()

def save_suggestion(session_id, content, variant="default"):
    """Save AI-generated suggestions to the database."""
    suggestion_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    with connect_db() as conn:
        conn.execute("""
        INSERT INTO suggestions (id, session_id, variant, content, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        (suggestion_id, session_id, variant, content, created_at))
    return suggestion_id

def save_serp(session_id, data_json):
    """Save SERP data to the database."""
    serp_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    with connect_db() as conn:
        conn.execute("""
        INSERT INTO serps (id, session_id, data, created_at)
        VALUES (?, ?, ?, ?)""",
        (serp_id, session_id, data_json, created_at))
    return serp_id

def get_suggestions_by_session(session_id):
    """Retrieve all suggestions for a given session."""
    with connect_db() as conn:
        rows = conn.execute("""
        SELECT id, variant, content, created_at 
        FROM suggestions 
        WHERE session_id = ? 
        ORDER BY created_at DESC
        """, (session_id,))
        return rows.fetchall()

def get_serp_by_session(session_id):
    """Retrieve SERP data for a given session."""
    with connect_db() as conn:
        row = conn.execute("""
        SELECT id, data, created_at 
        FROM serps 
        WHERE session_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
        """, (session_id,))
        return row.fetchone()

def get_full_session_data(session_id):
    """
    Retrieve complete session data including session, brief, suggestions, and SERP.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Dictionary with session, brief, suggestions, and serp data
    """
    with connect_db() as conn:
        # Get session data
        session_row = conn.execute("""
        SELECT id, created_at, topic 
        FROM sessions 
        WHERE id = ?
        """, (session_id,)).fetchone()
        
        # Get brief data  
        brief_row = conn.execute("""
        SELECT id, session_id, content, created_at 
        FROM briefs 
        WHERE session_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
        """, (session_id,)).fetchone()
        
        # Get suggestions
        suggestions_rows = conn.execute("""
        SELECT id, session_id, variant, content, created_at 
        FROM suggestions 
        WHERE session_id = ? 
        ORDER BY created_at DESC
        """, (session_id,)).fetchall()
        
        # Get SERP data
        serp_row = conn.execute("""
        SELECT id, session_id, data, created_at 
        FROM serps 
        WHERE session_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
        """, (session_id,)).fetchone()
        
        # Convert to dictionaries
        session_dict = None
        if session_row:
            session_dict = {
                "id": session_row[0],
                "created_at": session_row[1], 
                "topic": session_row[2]
            }
        
        brief_dict = None
        if brief_row:
            brief_dict = {
                "id": brief_row[0],
                "session_id": brief_row[1],
                "content": brief_row[2],
                "created_at": brief_row[3]
            }
        
        suggestions_list = []
        for row in suggestions_rows:
            suggestions_list.append({
                "id": row[0],
                "session_id": row[1], 
                "variant": row[2],
                "content": row[3],
                "created_at": row[4]
            })
        
        serp_dict = None
        if serp_row:
            serp_dict = {
                "id": serp_row[0],
                "session_id": serp_row[1],
                "data": serp_row[2],
                "created_at": serp_row[3]
            }
        
        return {
            "session": session_dict,
            "brief": brief_dict,
            "suggestions": suggestions_list,
            "serp": serp_dict
        }
