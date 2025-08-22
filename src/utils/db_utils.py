"""
Database utilities for the AI Keyword Tool.
Simplified database operations with proper error handling.
"""

import sqlite3
import uuid
import os
from datetime import datetime

# Database file in the main project directory
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app_data.db")

def connect_db():
    """Connect to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def safe_init_db():
    """Safely initialize database with fallback handling."""
    try:
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
            # Create suggestions table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                variant TEXT,
                content TEXT,
                created_at TEXT
            );
            """)
            # Create serps table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS serps (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                data TEXT,
                created_at TEXT
            );
            """)
            print("Database initialized with all tables.")
            return True
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        return False

def safe_save_session(topic):
    """Safely save a session to database with fallback handling."""
    try:
        session_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        with connect_db() as conn:
            conn.execute("INSERT INTO sessions (id, created_at, topic) VALUES (?, ?, ?)",
                        (session_id, created_at, topic))
        return session_id
    except Exception as e:
        print(f"Warning: Could not save session to database: {e}")
        return None

def safe_save_brief(session_id, content):
    """Safely save a brief to database with fallback handling."""
    if not session_id:
        return False
    try:
        brief_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        with connect_db() as conn:
            conn.execute("INSERT INTO briefs (id, session_id, content, created_at) VALUES (?, ?, ?, ?)",
                        (brief_id, session_id, content, created_at))
        return True
    except Exception as e:
        print(f"Warning: Could not save brief to database: {e}")
        return False

def safe_get_recent_sessions(limit=5):
    """Safely get recent sessions from database with fallback handling."""
    try:
        with connect_db() as conn:
            rows = conn.execute("SELECT id, topic, created_at FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
            return rows.fetchall()
    except Exception as e:
        print(f"Warning: Could not retrieve sessions from database: {e}")
        return []

def safe_save_suggestion(session_id, content, variant="default"):
    """Safely save AI suggestions to database with fallback handling."""
    if not session_id:
        return None
    try:
        suggestion_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        with connect_db() as conn:
            conn.execute("""
            INSERT INTO suggestions (id, session_id, variant, content, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (suggestion_id, session_id, variant, content, created_at))
        return suggestion_id
    except Exception as e:
        print(f"Warning: Could not save suggestion to database: {e}")
        return None

def safe_save_serp(session_id, data_json):
    """Safely save SERP data to database with fallback handling."""
    if not session_id:
        return None
    try:
        serp_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        with connect_db() as conn:
            conn.execute("""
            INSERT INTO serps (id, session_id, data, created_at)
            VALUES (?, ?, ?, ?)""",
            (serp_id, session_id, data_json, created_at))
        return serp_id
    except Exception as e:
        print(f"Warning: Could not save SERP data to database: {e}")
        return None

def safe_get_suggestions_by_session(session_id):
    """Safely get suggestions for a session with fallback handling."""
    if not session_id:
        return []
    try:
        with connect_db() as conn:
            rows = conn.execute("""
            SELECT id, variant, content, created_at 
            FROM suggestions 
            WHERE session_id = ? 
            ORDER BY created_at DESC
            """, (session_id,))
            return rows.fetchall()
    except Exception as e:
        print(f"Warning: Could not retrieve suggestions from database: {e}")
        return []

def safe_get_serp_by_session(session_id):
    """Safely get SERP data for a session with fallback handling."""
    if not session_id:
        return None
    try:
        with connect_db() as conn:
            row = conn.execute("""
            SELECT id, data, created_at 
            FROM serps 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """, (session_id,))
            return row.fetchone()
    except Exception as e:
        print(f"Warning: Could not retrieve SERP data from database: {e}")
        return None

def safe_get_full_session_data(session_id):
    """
    Safely retrieve complete session data with fallback handling.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Dictionary with session, brief, suggestions, and serp data or None if error
    """
    if not session_id:
        return None
        
    try:
        # Try to import and use the core database function with proper path handling
        import sys
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ai_tool_dir = os.path.join(base_dir, 'ai-keyword-tool')
        if ai_tool_dir not in sys.path:
            sys.path.append(ai_tool_dir)
        
        from core.db import get_full_session_data
        return get_full_session_data(session_id)
        
    except Exception as e:
        print(f"Warning: Could not retrieve full session data: {e}")
        
        # Fallback: try to get data manually with local connection
        try:
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
                
        except Exception as fallback_error:
            print(f"Warning: Fallback session data retrieval also failed: {fallback_error}")
            return None