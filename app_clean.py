# app.py - Clean Version
# AI Keyword Strategy Generator with Modern Dashboard
import streamlit as st
from src.ui.step_renderers import render_current_step
from src.core.state_manager import state_manager
from src.utils.db_utils import safe_init_db

# Initialize database on app startup
safe_init_db()

# Page config
st.set_page_config(
    page_title="AI Content Studio", 
    page_icon="✨", 
    layout="centered"
)

# Initialize centralized state management
state_manager._initialize_state()

# Add top banner
st.markdown("""
<div style="text-align: center; padding: 1.5rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 2rem;">
<h1 style="color: white; margin: 0; font-size: 2rem;">✨ AI Keyword Strategy Tool</h1>
<p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1rem;">Smart SEO Content Strategy & Content Creation</p>
</div>
""", unsafe_allow_html=True)

# Custom CSS for better styling
st.markdown("""
<style>
section.main .block-container { max-width: 1000px; padding-top: 1rem; }
h1 { color: #1e293b; margin-bottom: 1rem !important; }
h2 { margin-top: 1.5rem !important; margin-bottom: .75rem !important; color: #334155; }
h3 { margin-top: 1.2rem !important; margin-bottom: .6rem !important; color: #475569; }
.stButton > button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# Render current step using our clean renderer
render_current_step()

# Simple footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 1rem 0;">
🤖 Powered by AI • Built for Content Creators
</div>
""", unsafe_allow_html=True)