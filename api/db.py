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


def init_serp_cache_table():
    """Create SERP cache table if it does not already exist."""
    with get_conn() as conn:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS serp_cache (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          keyword TEXT NOT NULL,
          country TEXT DEFAULT 'US',
          language TEXT DEFAULT 'en',
          serp_data TEXT,              -- Full SERP response as JSON
          organic_results TEXT,        -- Top 10 organic results as JSON
          search_intent TEXT,          -- Detected search intent
          competition_analysis TEXT,   -- Competition analysis as JSON
          difficulty_score INTEGER,    -- Calculated difficulty score (0-100)
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now')),
          UNIQUE(keyword, country, language)
        );
        """
        )
        # Create index for faster lookups
        conn.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_serp_cache_lookup 
        ON serp_cache(keyword, country, language);
        """
        )
        # Create index for TTL cleanup
        conn.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_serp_cache_created 
        ON serp_cache(created_at);
        """
        )


def init_brief_cache_table():
    """Create brief cache table if it does not already exist."""
    with get_conn() as conn:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS brief_cache (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          keyword TEXT NOT NULL,
          variant TEXT DEFAULT 'a',     -- Variant 'a' or 'b'
          brief_data TEXT,              -- Full structured brief as JSON
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now')),
          UNIQUE(keyword, variant)
        );
        """
        )
        # Create index for faster lookups
        conn.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_brief_cache_lookup 
        ON brief_cache(keyword, variant);
        """
        )
        # Create index for TTL cleanup
        conn.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_brief_cache_created 
        ON brief_cache(created_at);
        """
        )


def get_serp_cache(keyword: str, country: str = "US", language: str = "en", ttl_hours: int = 24) -> dict | None:
    """Get cached SERP data if exists and not expired."""
    import json
    
    with get_conn() as conn:
        cursor = conn.execute(
            """
            SELECT serp_data, organic_results, search_intent, competition_analysis, difficulty_score, created_at
            FROM serp_cache 
            WHERE keyword = ? AND country = ? AND language = ?
            AND datetime(created_at, '+' || ? || ' hours') > datetime('now')
            """,
            (keyword, country, language, ttl_hours)
        )
        row = cursor.fetchone()
        
        if row:
            try:
                return {
                    "serp": json.loads(row[0]) if row[0] else None,
                    "organic_results": json.loads(row[1]) if row[1] else None,
                    "search_intent": row[2],
                    "competition_analysis": json.loads(row[3]) if row[3] else None,
                    "difficulty_score": row[4],
                    "cached_at": row[5],
                    "from_cache": True
                }
            except json.JSONDecodeError:
                # If JSON is corrupted, ignore cache entry
                pass
    
    return None


def set_serp_cache(
    keyword: str, 
    country: str, 
    language: str, 
    serp_data: dict, 
    organic_results: list = None,
    search_intent: str = None,
    competition_analysis: dict = None,
    difficulty_score: int = None
) -> None:
    """Store SERP data in cache."""
    import json
    
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO serp_cache 
            (keyword, country, language, serp_data, organic_results, search_intent, competition_analysis, difficulty_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                keyword,
                country,
                language,
                json.dumps(serp_data) if serp_data else None,
                json.dumps(organic_results) if organic_results else None,
                search_intent,
                json.dumps(competition_analysis) if competition_analysis else None,
                difficulty_score
            )
        )


def cleanup_expired_serp_cache(ttl_hours: int = 24) -> int:
    """Remove expired SERP cache entries. Returns number of deleted rows."""
    with get_conn() as conn:
        cursor = conn.execute(
            """
            DELETE FROM serp_cache 
            WHERE datetime(created_at, '+' || ? || ' hours') <= datetime('now')
            """,
            (ttl_hours,)
        )
        return cursor.rowcount


def get_brief_cache(keyword: str, variant: str = "a", ttl_hours: int = 168) -> dict | None:
    """Get cached brief data if exists and not expired. Default TTL is 7 days (168 hours)."""
    import json
    
    with get_conn() as conn:
        cursor = conn.execute(
            """
            SELECT brief_data, created_at
            FROM brief_cache 
            WHERE keyword = ? AND variant = ?
            AND datetime(created_at, '+' || ? || ' hours') > datetime('now')
            """,
            (keyword, variant, ttl_hours)
        )
        row = cursor.fetchone()
        
        if row:
            try:
                return {
                    "brief": json.loads(row[0]),
                    "cached_at": row[1],
                    "from_cache": True
                }
            except json.JSONDecodeError:
                # If JSON is corrupted, ignore cache entry
                pass
    
    return None


def set_brief_cache(keyword: str, variant: str, brief_data: dict) -> None:
    """Store brief data in cache."""
    import json
    
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO brief_cache 
            (keyword, variant, brief_data, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (
                keyword,
                variant,
                json.dumps(brief_data)
            )
        )


def cleanup_expired_brief_cache(ttl_hours: int = 168) -> int:
    """Remove expired brief cache entries. Returns number of deleted rows."""
    with get_conn() as conn:
        cursor = conn.execute(
            """
            DELETE FROM brief_cache 
            WHERE datetime(created_at, '+' || ? || ' hours') <= datetime('now')
            """,
            (ttl_hours,)
        )
        return cursor.rowcount

