"""
Cache management for the AI Keyword Tool.
Enhanced with smart caching, dependency tracking, and performance optimization.
"""

import streamlit as st
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class CacheManager:
    """Enhanced cache manager with smart caching and dependency tracking."""
    
    def __init__(self):
        # Initialize session cache
        if "cache" not in st.session_state:
            st.session_state.cache = {}
        if "cache_metadata" not in st.session_state:
            st.session_state.cache_metadata = {}
        
        # Initialize persistent cache database
        self.db_path = Path("data/cache.db")
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_persistent_cache()
    
    def _init_persistent_cache(self):
        """Initialize persistent cache database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_dependencies (
                    cache_key TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'data'
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Cache database initialization error: {e}")
    
    def generate_smart_key(self, data_type: str, keyword: str, **params) -> str:
        """Generate a smart cache key with consistent hashing."""
        cache_params = {
            "keyword": keyword.lower().strip(),
            "data_type": data_type,
            **params
        }
        
        cache_string = json.dumps(cache_params, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()[:12]
        
        return f"{data_type}_{cache_hash}"
    
    def get(self, key: str) -> Any:
        """Get value from session cache."""
        return st.session_state.cache.get(key)
    
    def set(self, key: str, value: Any, data_type: str = "generic", keyword: str = "", expires_hours: int = 24):
        """Set value in session cache with metadata."""
        st.session_state.cache[key] = value
        st.session_state.cache_metadata[key] = {
            "data_type": data_type,
            "keyword": keyword,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        }
    
    def get_smart_cached(self, data_type: str, keyword: str, max_age_hours: int = 24, **params) -> Optional[Any]:
        """Get cached data with smart key generation and age checking."""
        cache_key = self.generate_smart_key(data_type, keyword, **params)
        
        # Check session cache first
        if cache_key in st.session_state.cache:
            metadata = st.session_state.cache_metadata.get(cache_key, {})
            if metadata:
                try:
                    created_at = datetime.fromisoformat(metadata["created_at"])
                    age = datetime.now() - created_at
                    if age < timedelta(hours=max_age_hours):
                        return st.session_state.cache[cache_key]
                except:
                    pass
        
        # Check persistent cache
        return self._get_persistent_cached(cache_key, max_age_hours)
    
    def set_smart_cached(self, data_type: str, keyword: str, value: Any, expires_hours: int = 24, **params):
        """Set cached data with smart key generation."""
        cache_key = self.generate_smart_key(data_type, keyword, **params)
        
        # Set in session cache
        self.set(cache_key, value, data_type, keyword, expires_hours)
        
        # Set in persistent cache
        self._set_persistent_cached(cache_key, data_type, keyword, value, expires_hours)
    
    def _get_persistent_cached(self, cache_key: str, max_age_hours: int) -> Optional[Any]:
        """Get from persistent cache database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data_json, created_at FROM cache_entries 
                WHERE cache_key = ? AND created_at > datetime('now', '-{} hours')
            """.format(max_age_hours), (cache_key,))
            
            row = cursor.fetchone()
            if row:
                # Update access count
                cursor.execute("""
                    UPDATE cache_entries SET access_count = access_count + 1 
                    WHERE cache_key = ?
                """, (cache_key,))
                conn.commit()
                conn.close()
                
                return json.loads(row[0])
            
            conn.close()
            return None
        except Exception:
            return None
    
    def _set_persistent_cached(self, cache_key: str, data_type: str, keyword: str, value: Any, expires_hours: int):
        """Set in persistent cache database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            data_json = json.dumps(value, default=str)
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            cursor.execute("""
                INSERT OR REPLACE INTO cache_entries 
                (cache_key, data_type, keyword, data_json, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, data_type, keyword, data_json, expires_at))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Persistent cache error: {e}")
    
    def invalidate_keyword_cache(self, keyword: str):
        """Invalidate all cache entries for a specific keyword."""
        # Clear from session cache
        keys_to_remove = []
        for key, metadata in st.session_state.cache_metadata.items():
            if metadata.get("keyword", "").lower() == keyword.lower():
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            st.session_state.cache.pop(key, None)
            st.session_state.cache_metadata.pop(key, None)
        
        # Clear from persistent cache
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache_entries WHERE keyword = ?", (keyword.lower(),))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        session_entries = len(st.session_state.cache)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM cache_entries WHERE expires_at > datetime('now')")
            persistent_entries = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT data_type, COUNT(*) FROM cache_entries 
                WHERE expires_at > datetime('now') 
                GROUP BY data_type
            """)
            by_type = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "session_entries": session_entries,
                "persistent_entries": persistent_entries,
                "by_type": by_type,
                "total_entries": session_entries + persistent_entries
            }
        except Exception:
            return {
                "session_entries": session_entries,
                "persistent_entries": 0,
                "by_type": {},
                "total_entries": session_entries
            }
    
    def clear(self):
        """Clear all cache."""
        st.session_state.cache = {}
        st.session_state.cache_metadata = {}
        
        # Clear persistent cache
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache_entries")
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        # Clean session cache
        current_time = datetime.now()
        keys_to_remove = []
        
        for key, metadata in st.session_state.cache_metadata.items():
            try:
                expires_at = datetime.fromisoformat(metadata["expires_at"])
                if current_time > expires_at:
                    keys_to_remove.append(key)
            except:
                keys_to_remove.append(key)  # Remove invalid entries
        
        for key in keys_to_remove:
            st.session_state.cache.pop(key, None)
            st.session_state.cache_metadata.pop(key, None)
        
        # Clean persistent cache
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache_entries WHERE expires_at < datetime('now')")
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted_count
        except Exception:
            return 0
    
    def render_cache_info(self):
        """Render enhanced cache information in sidebar."""
        if st.session_state.get("dev_mode"):
            stats = self.get_cache_stats()
            st.sidebar.write(f"Cache entries: {stats['total_entries']}")
            st.sidebar.write(f"Session: {stats['session_entries']}, Persistent: {stats['persistent_entries']}")
            
            if stats["by_type"]:
                st.sidebar.write("By type:")
                for data_type, count in stats["by_type"].items():
                    st.sidebar.write(f"  {data_type}: {count}")

def cached(func: Callable) -> Callable:
    """Decorator for caching function results."""
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        key_data = {
            "func": func.__name__,
            "args": args,
            "kwargs": kwargs
        }
        key = hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
        
        # Check cache
        cached_result = cache_manager.get(key)
        if cached_result is not None:
            return cached_result
        
        # Execute and cache
        result = func(*args, **kwargs)
        cache_manager.set(key, result)
        return result
    
    return wrapper

# Global instance
cache_manager = CacheManager()