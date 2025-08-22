"""
State management for the AI Keyword Tool.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    """Application configuration."""
    default_country: str = "US"
    default_language: str = "en"
    max_keywords: int = 50
    
class StateManager:
    """Manages application state across Streamlit sessions."""
    
    def __init__(self):
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize session state variables."""
        defaults = {
            "ux_step": 1,
            "help_open": False,
            "help_step": 1,
            "seed_input": "",
            "industry_input": "",
            "audience_input": "",
            "country_input": "US",
            "language_input": "en",
            "selected_keyword": "",
            "keywords_data": None,
            "brief_output": "",
            "brief_variant": "A",
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @property
    def current_step(self) -> int:
        """Get current UX step."""
        return st.session_state.get("ux_step", 1)
    
    def go_to_step(self, step: int):
        """Navigate to a specific step."""
        st.session_state.ux_step = step
        st.rerun()
    
    def open_help(self, step: Optional[int] = None):
        """Open help dialog."""
        st.session_state.help_open = True
        if step:
            st.session_state.help_step = step
    
    def close_help(self):
        """Close help dialog."""
        st.session_state.help_open = False
    
    def set_selected_keyword(self, keyword: str):
        """Set the selected keyword."""
        st.session_state.selected_keyword = keyword
    
    def ensure_keyword_service(self):
        """Ensure keyword service is available."""
        # Placeholder for service initialization
        pass

# Global instance
state_manager = StateManager()