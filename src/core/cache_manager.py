"""
Cache management for the AI Keyword Tool.
"""

import streamlit as st
from typing import Any, Callable
import hashlib
import json

class CacheManager:
    """Manages caching for expensive operations."""
    
    def __init__(self):
        if "cache" not in st.session_state:
            st.session_state.cache = {}
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        return st.session_state.cache.get(key)
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        st.session_state.cache[key] = value
    
    def clear(self):
        """Clear all cache."""
        st.session_state.cache = {}
    
    def render_cache_info(self):
        """Render cache information in sidebar."""
        if st.session_state.get("dev_mode"):
            st.sidebar.write(f"Cache entries: {len(st.session_state.cache)}")

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