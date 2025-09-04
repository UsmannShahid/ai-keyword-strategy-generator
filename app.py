# app.py
# ---------------------------------------------
# AI Keyword Strategy Generator (SLC v1.1)
# - Personalized inputs (industry, audience, location)
# - JSON output from model -> clean table + CSV download
# - Robust error handling + helpful comments
# ---------------------------------------------

import os
import json
from datetime import datetime
from typing import Optional, List
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from src.ui.ui_helpers import render_copy_from_dataframe
from src.core.services import KeywordService, generate_writer_notes, generate_brief_with_variant, fetch_serp_snapshot
from src.utils.parsing import SAFE_OUTPUT, parse_brief_output, detect_placeholders
from src.utils.utils import slugify, default_report_name
from src.core.prompt_manager import prompt_manager
from src.utils.scoring import add_scores, quickwin_breakdown, explain_quickwin
from src.utils.eval_logger import log_eval
from src.utils.brief_renderer import brief_to_markdown_full
from src.utils.serp_utils import analyze_serp
from src.core.state_manager import state_manager, AppConfig
from src.ui.step_renderers import render_current_step
from src.core.cache_manager import cache_manager



# OpenAI SDK (current usage style)
# pip install --upgrade openai
from openai import OpenAI

# Initialize database on app startup
from src.utils.db_utils import safe_init_db
safe_init_db()

# --- GLOBAL UX: hero + state ---
st.set_page_config(page_title="Keyword Quick Wins + AI Brief", page_icon="✨", layout="centered")

# Initialize session state FIRST - before any other operations
# Essential session state variables that must be available immediately
essential_state = {
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
    "serp_data": None,
    "selected_keyword_source": "AI Generated"
}

for key, default_value in essential_state.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# Initialize centralized state management
# This replaces all the individual session state initializations

# Ensure state manager is properly initialized
if not hasattr(state_manager, '_initialized'):
    state_manager._initialized = True

def _open_help(step: Optional[int] = None):
    state_manager.open_help(step)

def _close_help():
    state_manager.close_help()



def _current_step_help():
    step = st.session_state.get("help_step", 1)
    kw = st.session_state.get("selected_keyword") or st.session_state.get("seed_input") or "your topic"
    if step == 1:
        return {
            "title": "Step 1 — Inputs",
            "why": [
                "Clear inputs → better keyword discovery & intent match.",
                "Country/language alignment avoids chasing irrelevant SERPs."
            ],
            "how": [
                "Use a **broad seed** (e.g., 'ergonomic chair').",
                "Fill **country/language** for localized SERPs.",
                "Describe audience to bias toward buyer vs. info intent."
            ],
            "tips": [
                "Avoid super‑niche seeds; you'll filter in Step 2.",
                "Add 1–2 industry terms to improve related entities."
            ],
            "example": [
                "Seed: `home office chairs`",
                "Audience: `remote workers`  · Country: `US` · Language: `en`"
            ]
        }
    elif step == 2:
        return {
            "title": "Step 2 — Quick‑Win Keywords",
            "why": [
                "Quick‑Win score highlights rankable opportunities.",
                "Intent lets you prioritize buyer vs. info pages."
            ],
            "how": [
                "Raise **Min score** to 60–80 to focus on winnable terms.",
                "Use **Include/Exclude** to tighten topical focus.",
                "Pick a keyword → we'll generate a brief automatically."
            ],
            "tips": [
                "Prefer **specific** modifiers (size, price, 'near me').",
                "Scan SERP for outdated/weak results to confirm opportunity."
            ],
            "example": [
                "Selected: `affordable pool cleaning near me`",
                "Reason: high intent + local modifier + decent volume."
            ]
        }
    # step 3
    return {
        "title": "Step 3 — AI Content Brief",
        "why": [
            "Structured briefs speed writing and improve on‑page SEO.",
            "Consistent H2/H3 + entities → better topical coverage."
        ],
        "how": [
            "Choose Variant **A** for stricter SEO; **B** for writer tone.",
            "Download Markdown and share with your writer/CMS.",
            "Rate the brief to improve prompts over time."
        ],
        "tips": [
            "Add internal links to money pages.",
            "If SERP leaders are thin/outdated, expand sections and add FAQs."
        ],
        "example": [
            f"Briefing: `{kw}`",
            "Includes: Title, Meta, Outline, Entities, Links, FAQs."
        ]
    }

@st.dialog("Help & Guidance")  # modern Streamlit dialog
def _help_dialog():
    data = _current_step_help()
    st.markdown(f"### {data['title']}")
    tabs = st.tabs(["Overview", "Why this helps SEO", "How to use", "Pro tips", "Example"])
    with tabs[0]:
        st.write(
            "- **Find** low‑competition, high‑intent keywords\n"
            "- **Choose** one with the best Quick‑Win score\n"
            "- **Generate** a clean, writer‑ready brief\n"
            "- **A/B test** prompts, **rate**, and **log**"
        )
    with tabs[1]:
        for x in data["why"]: st.markdown(f"- {x}")
    with tabs[2]:
        for x in data["how"]: st.markdown(f"- {x}")
    with tabs[3]:
        for x in data["tips"]: st.markdown(f"- {x}")
    with tabs[4]:
        for x in data["example"]: st.markdown(f"- {x}")
    st.divider()
    if st.button("Close", type="primary"):
        _close_help()


# Helper functions for navigation
def _go(step: int):
    state_manager.go_to_step(step)

def _on_keyword_pick():
    pick = st.session_state.get("kw_pick_select")
    if pick:
        state_manager.set_selected_keyword(pick)
        state_manager.go_to_step(3)
        st.toast(f"Keyword selected: {pick}")
        st.rerun()

# SVG Icons
ICON_BRIEF = """<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"
  xmlns="http://www.w3.org/2000/svg" style="vertical-align:-2px;">
  <path d="M8 4h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM8 6v12h8V6H8zm2 2h4v1H10V8zm0 3h4v1H10v-1zm0 3h2v1H10v-1z"/></svg>"""

# Guided onboarding for new users
def render_welcome_onboarding():
    """Welcome screen for first-time users"""
    st.markdown("""
    <div style="text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; margin-bottom: 2rem; color: white;">
    <h1 style="margin: 0; font-size: 2.5rem;">✨ Welcome to AI Keyword Tool</h1>
    <p style="font-size: 1.2rem; margin: 1rem 0 2rem 0; opacity: 0.9;">Get more customers by creating content that people actually search for</p>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin: 2rem 0;">
        <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 12px;">
            <h3>🔍 Find Keywords</h3>
            <p>Discover what your customers are searching for</p>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 12px;">
            <h3>📋 Get Content Plans</h3>
            <p>AI creates detailed guides for your content</p>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 12px;">
            <h3>🏆 Beat Competition</h3>
            <p>See what competitors are doing and do it better</p>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick path selection for different user types
    st.markdown("### 🎯 What brings you here today?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 I need more customers", use_container_width=True, type="primary"):
            st.session_state.user_intent = "growth"
            st.session_state.show_onboarding = False
            st.session_state.selected_workflow = "keyword_research"
            st.rerun()
            
    with col2:  
        if st.button("📝 I need content ideas", use_container_width=True):
            st.session_state.user_intent = "content"
            st.session_state.show_onboarding = False  
            st.session_state.selected_workflow = "content_ideas"
            st.rerun()
            
    with col3:
        if st.button("⚡ I need this done fast", use_container_width=True):
            st.session_state.user_intent = "speed"
            st.session_state.show_onboarding = False
            st.session_state.selected_workflow = "quick_brief" 
            st.rerun()
    
    st.markdown("---")
    
    # Value propositions based on user type
    intent = st.session_state.get("user_intent", "")
    if intent == "growth":
        st.success("🎯 **Perfect!** We'll help you find keywords that bring paying customers, not just traffic.")
    elif intent == "content":
        st.info("💡 **Great choice!** We'll generate content ideas that your audience actually wants to read.")
    elif intent == "speed":
        st.warning("⚡ **Let's go!** Skip the research and get straight to actionable content plans.")
    
    if st.checkbox("Don't show this welcome screen again"):
        st.session_state.hide_onboarding_permanently = True

def handle_error_with_recovery(error_msg, error_type="general", step=None):
    """Enhanced error handling with recovery suggestions"""
    
    if error_type == "api_limit":
        st.error(f"⚠️ **API Limit Reached**")
        st.markdown("""
        **What happened:** You've reached your daily limit for this feature.
        
        **What you can do:**
        - 🔄 Try again tomorrow for fresh limits
        - 💎 Upgrade to Premium for higher limits
        - ✍️ Use manual keyword entry as a workaround
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again Tomorrow", help="Reset will be automatic"):
                st.info("Your limits reset at midnight UTC")
        with col2:
            if st.button("✍️ Enter Keywords Manually"):
                st.session_state.manual_keyword_mode = True
                st.rerun()
                
    elif error_type == "network":
        st.error(f"🌐 **Connection Issue**")
        st.markdown("""
        **What happened:** We couldn't connect to our services.
        
        **What you can do:**
        - 🔄 Check your internet connection
        - ⏰ Wait a moment and try again
        - 💾 Your progress is saved automatically
        """)
        
        if st.button("🔄 Retry Now", type="primary"):
            st.rerun()
            
    elif error_type == "generation":
        st.error(f"🤖 **Generation Error**")
        st.markdown(f"""
        **What happened:** {error_msg}
        
        **What you can do:**
        - 🔄 Try with different keywords
        - ✍️ Provide more business details
        - 📞 Contact support if this persists
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Different Keywords"):
                if step:
                    state_manager.go_to_step(step - 1)
                st.rerun()
        with col2:
            if st.button("✍️ Add More Details"):
                state_manager.go_to_step(1)
                st.rerun()
    else:
        # Generic error with helpful recovery
        st.error(f"❌ **Something went wrong**")
        st.markdown(f"""
        **Error details:** {error_msg}
        
        **What you can try:**
        - 🔄 Refresh the page and try again
        - 🔙 Go back to the previous step
        - 💾 Your progress has been saved
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh & Retry"):
                st.rerun()
        with col2:
            if st.button("🔙 Go Back") and step and step > 1:
                state_manager.go_to_step(step - 1)
                st.rerun()

def show_progress_celebration(step, keyword=None):
    """Motivational progress celebrations"""
    celebrations = {
        1: {
            "title": "🎉 Great start!",
            "message": "You've set up your business context. Now let's find some amazing keywords!",
            "tip": "💡 The more specific you are, the better keywords we'll find."
        },
        2: {
            "title": "🚀 Keywords discovered!", 
            "message": f"Found opportunities for {keyword or 'your business'}. Time to pick your winner!",
            "tip": "🎯 Look for green scores (70+) - these are your quick wins!"
        },
        3: {
            "title": "📋 Content plan ready!",
            "message": f"Your content brief for '{keyword}' is complete. You're almost done!",
            "tip": "✅ This brief will guide you to create content that ranks."
        },
        4: {
            "title": "🔍 Competition analyzed!",
            "message": "Now you know exactly what your competitors are doing. Time for strategy!",
            "tip": "💪 Use these insights to create better content than your competition."
        },
        5: {
            "title": "🏆 Mission accomplished!",
            "message": "You have everything needed to dominate your market. Go create amazing content!",
            "tip": "📈 Track your rankings and come back for more keywords when you're ready."
        }
    }
    
    if step in celebrations:
        celebration = celebrations[step]
        
        # Animated celebration
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
            color: white; 
            padding: 1.5rem; 
            border-radius: 12px; 
            text-align: center; 
            margin: 1rem 0;
            animation: celebrationPulse 2s ease-in-out;
        ">
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.5rem;">{celebration['title']}</h3>
            <p style="margin: 0 0 1rem 0; font-size: 1.1rem; opacity: 0.95;">{celebration['message']}</p>
            <small style="opacity: 0.9;">{celebration['tip']}</small>
        </div>
        
        <style>
        @keyframes celebrationPulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.02); opacity: 1; }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Progress stats
        progress_percentage = (step / 5) * 100
        if step < 5:
            st.progress(progress_percentage / 100, f"Progress: {progress_percentage:.0f}% complete")
        else:
            st.success("🎯 **100% Complete!** You're ready to dominate your market!")
            
            # Completion rewards
            if st.button("🎁 Get Your Success Kit", type="primary"):
                st.balloons()
                st.success("🎉 Congratulations! Check your downloads for your complete strategy.")

def add_helpful_tooltips():
    """Add contextual help tooltips throughout the app"""
    
    # Add CSS for tooltips
    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #1e293b;
        color: white;
        text-align: center;
        padding: 8px;
        border-radius: 6px;
        font-size: 12px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)

# Check if we should show onboarding
show_onboarding = st.session_state.get("show_onboarding", True)
hide_permanently = st.session_state.get("hide_onboarding_permanently", False)

if show_onboarding and not hide_permanently:
    render_welcome_onboarding()
else:
    # Original hero section for returning users
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 12px; margin-bottom: 2rem; border: 1px solid #cbd5e1;">
    <h2 style="color: #1e293b; margin: 0; font-size: 2rem;">✨ AI Keyword Strategy Generator</h2>
    <p style="color: #64748b; font-size: 1.1rem; margin: 0.5rem 0 0 0;">Find quick-win keywords → Generate content briefs → Analyze competition → Get actionable insights</p>
    </div>
    """, unsafe_allow_html=True)

# header bar: Help button on the right with better styling
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("❓ Need Help?", key="main_help_button", help="Get guidance for the current step"):
        _open_help(state_manager.current_step)

# Render dialog if flagged
if st.session_state.get("help_open", False):
    _help_dialog()
    # Reset the help_open state after showing dialog to prevent repeated popups
    st.session_state.help_open = False


def step_header():
    s = st.session_state.get("ux_step", 1)
    selected_kw = st.session_state.get("selected_keyword", "")
    
    # Clean, simple header without progress indicator
    steps = ["📝 Business", "🔍 Keywords", "📋 Content", "🏆 Competition", "✨ Strategy"]
    current_step_name = steps[s-1] if s <= len(steps) else "Progress"
    
    if selected_kw:
        st.success(f"🎯 **{current_step_name}:** {selected_kw}")
    else:
        st.info(f"📍 **{current_step_name}** (Step {s} of 5)")
    
    st.divider()

# Custom CSS for better reading width and spacing
st.markdown("""
<style>
section.main .block-container { max-width: 1200px; padding-top: 2rem; }

/* improved heading spacing and typography */
h1 { color: #1e293b; margin-bottom: 1rem !important; }
h2 { margin-top: 1.5rem !important; margin-bottom: .75rem !important; color: #334155; }
h3 { margin-top: 1.2rem !important; margin-bottom: .6rem !important; color: #475569; }

/* better form spacing */
.stSelectbox > div > div { margin-bottom: 1rem; }
.stTextInput > div > div { margin-bottom: 1rem; }

/* improved button styling */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

/* better info/warning boxes */
.stAlert {
    border-radius: 8px !important;
    border-left: 4px solid !important;
}

/* improved metric display */
.metric-container {
    background: #f8fafc;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    text-align: center;
}

/* keyword/intents badges - improved contrast */
.k-badge { display:inline-block; padding:4px 12px; border-radius:20px; font-weight:600; font-size:12px; border: 1px solid; }
.k-badge--buy { background:#dcfce7; color:#166534; border-color:#bbf7d0; }
.k-badge--info { background:#dbeafe; color:#1e40af; border-color:#93c5fd; }
.k-badge--brand { background:#fef3c7; color:#a16207; border-color:#fcd34d; }
.k-badge--weak { background:#fee2e2; color:#b91c1c; border-color:#fca5a5; }
.k-badge--strong { background:#d1fae5; color:#15803d; border-color:#86efac; }

/* Clean header styling - no fancy stepper needed */
.step-header-container { margin-bottom: 1rem; }

/* Mobile optimization - responsive design */
@media (max-width: 768px) {
    section.main .block-container {
        max-width: 100%;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        padding-top: 1rem;
    }
    
    /* Mobile header optimization */
    .step-header-container {
        margin-bottom: 0.5rem;
    }
    
    /* Mobile buttons - touch friendly */
    .stButton > button {
        width: 100% !important;
        padding: 1rem !important;
        font-size: 16px !important;
        min-height: 48px !important;
    }
    
    /* Mobile forms - prevent zoom on iOS */
    .stTextInput > div > div input,
    .stTextArea > div > div textarea {
        font-size: 16px !important;
    }
    
    /* Mobile tables */
    .dataframe div[data-testid="stDataFrame"] {
        font-size: 12px;
        overflow-x: auto;
    }
}

@media (max-width: 480px) {
    /* Extra small screens */
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.25rem !important; }
}

/* Touch-friendly enhancements */
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

/* Focus accessibility */
.stButton > button:focus {
    outline: 2px solid #3b82f6 !important;
    outline-offset: 2px !important;
}

/* Loading states */
.stSpinner > div {
    border-color: #3b82f6 !important;
}
</style>
""", unsafe_allow_html=True)

# Color styling for intent categories - improved contrast
INTENT_COLORS = {
    "transactional": "#dcfce7",  # light green with better contrast
    "informational": "#dbeafe",  # light blue
    "navigational":  "#fef3c7",  # light amber
    "branded":       "#fce7f3",  # light pink
}


def style_intent(s: pd.Series):
    return [f"background-color: {INTENT_COLORS.get(v.lower(), '#f3f4f6')}" for v in s]


# ------------- One-time Setup --------------------
load_dotenv()  # Load environment variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Legacy compatibility (tests expect these symbols) ---
# Provide a lazily created OpenAI client & helper functions used in older tests.
client = None
try:
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
except Exception:
    client = None  # Tests will patch this.

def build_prompt(business_desc: str, industry: str = "", audience: str = "", location: str = "") -> str:
    """Legacy prompt builder retained for test suite.
    Returns instructions to produce valid JSON with informational, transactional, branded keys.
    """
    parts = [
        f"Business Description: {business_desc.strip()}",
    ]
    if industry:
        parts.append(f"Industry: {industry.strip()}")
    if audience:
        parts.append(f"Audience: {audience.strip()}")
    if location:
        parts.append(f"Location: {location.strip()}")
    parts.append(
        (
            "Return valid JSON with exactly these keys: informational, transactional, branded. "
            "Each value must be a list of keyword strings. Do NOT include explanations."
        )
    )
    return "\n".join(parts)

def get_keywords_json(prompt: str, plan_settings: dict = None):
    """Legacy helper expected by tests. Uses chat.completions style mocked in tests.
    Returns parsed JSON content from first choice; propagates JSON errors.
    """
    if client is None:
        raise RuntimeError("OpenAI client not initialized")
    
    # Use plan-specific model or default to gpt-4o-mini
    model = plan_settings.get("gpt_model", "gpt-4o-mini") if plan_settings else "gpt-4o-mini"
    
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    raw = resp.choices[0].message.content
    data = json.loads(raw)  # Let JSONDecodeError bubble up for tests
    return data

# Fail fast if key is missing, with a clear message
if not OPENAI_API_KEY:
    st.error("❌ Missing OPENAI_API_KEY. Add it to your .env file.")
    st.info("📝 Copy .env.example to .env and add your OpenAI API key")
    st.stop()

# Basic API key validation
if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-"):
    st.error("⚠️ API key format appears incorrect. OpenAI keys start with 'sk-'")
    st.stop()

# Title is now included in the hero section above

# No additional navigation needed - sidebar is simplified

# Keep a simple in-memory history for this session
if "history" not in st.session_state:
    st.session_state.history = []

# Keyword service initialization is now handled by state_manager.ensure_keyword_service()

# ------------- Small Utilities -------------------
# Note: slugify and default_report_name are imported from utils.py

def to_dataframe(data: dict) -> pd.DataFrame:
    """
    Convert the model's JSON structure into a flat table:
    columns: keyword | category
    """
    rows = []
    for category in ("informational", "transactional", "branded"):
        for kw in data.get(category, []) or []:
            rows.append({"keyword": kw, "category": category})
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["keyword", "category"])

# ------------- STEP RENDERERS ------------------------
# Step renderers moved to ui/step_renderers.py for better organization

# ------------- MAIN WIZARD FLOW ------------------------

# Display step header
step_header()

# Add user plan toggle for development/testing
st.markdown("### 🎯 Plan Selection (Dev Mode)")
user_plan = st.radio(
    "Choose your plan for testing:",
    ["free", "paid"],
    index=1,  # Default to paid for testing
    horizontal=True,
    help="This simulates free vs premium tier features. Later this will be pulled from database/auth system."
)

# Store in session state for access throughout the app
st.session_state.user_plan = user_plan

# Plan-based configuration object
PLAN_CONFIG = {
    "free": {
        "gpt_model": "gpt-3.5-turbo",
        "serp_provider": "searchapi",
        "keyword_analysis_enabled": False,
        "max_keywords": 10,
        "max_briefs_per_day": 3,
        "serp_results_limit": 5,
        "cache_ttl_hours": 6
    },
    "paid": {
        "gpt_model": "gpt-4",
        "serp_provider": "serpapi",
        "keyword_analysis_enabled": True,
        "max_keywords": 50,
        "max_briefs_per_day": 50,
        "serp_results_limit": 20,
        "cache_ttl_hours": 24
    }
}

# Get plan-specific settings
plan_settings = PLAN_CONFIG[user_plan]

# Store plan settings in session state for global access
st.session_state.plan_settings = plan_settings

# Visual indicator of current plan with features
if user_plan == "free":
    st.info(f"""
    🆓 **Free Plan Active**
    - Model: {plan_settings['gpt_model']}
    - SERP Provider: {plan_settings['serp_provider']}
    - Max Keywords: {plan_settings['max_keywords']}
    - Daily Briefs: {plan_settings['max_briefs_per_day']}
    """)
else:
    st.success(f"""
    💎 **Premium Plan Active**
    - Model: {plan_settings['gpt_model']}
    - SERP Provider: {plan_settings['serp_provider']}
    - Advanced Analysis: ✅
    - Unlimited Keywords & Briefs
    """)

st.divider()

# Initialize helpful features
add_helpful_tooltips()

# Admin Dashboard
if st.session_state.get("show_admin", False):
    import requests
    import pandas as pd
    from datetime import datetime
    
    st.title("⚙️ Admin Dashboard")
    
    # Back button
    if st.button("← Back to Main App"):
        st.session_state.show_admin = False
        st.rerun()
    
    st.divider()
    
    # API base URL
    API_BASE = "http://127.0.0.1:8001"
    
    # Admin key input
    admin_key = st.text_input("Admin Key", type="password", help="Enter your admin key to access analytics")
    
    if admin_key:
        headers = {"X-Admin-Key": admin_key}
        
        # Time range selector
        st.subheader("📊 Analytics Dashboard")
        days = st.selectbox("Time Range", [7, 30, 90, 365], index=1, format_func=lambda x: f"Last {x} days")
        
        col1, col2, col3 = st.columns(3)
        
        try:
            # Summary metrics
            with col1:
                st.markdown("### 📈 Summary")
                summary_resp = requests.get(f"{API_BASE}/admin/metrics/summary?days={days}", headers=headers, timeout=5)
                if summary_resp.status_code == 200:
                    summary = summary_resp.json()
                    st.metric("Total Events", summary["total_events"])
                    st.metric("Total Users", summary["total_users"])
                    st.metric("Paid Users", summary["paid_users"])
                    st.metric("Paid Ratio", f"{summary['paid_ratio']:.1%}")
                    st.metric("Total Tokens", f"{summary['tokens_total']:,}")
                    if summary["avg_latency_ms"]:
                        st.metric("Avg Latency", f"{summary['avg_latency_ms']:.0f}ms")
                else:
                    st.error(f"Error: {summary_resp.status_code}")
            
            # Event breakdown
            with col2:
                st.markdown("### 🔍 Event Breakdown")
                if summary_resp.status_code == 200:
                    counts = summary["counts"]
                    for event_type, count in counts.items():
                        st.metric(event_type.replace("_", " ").title(), count)
            
            # Top users
            with col3:
                st.markdown("### 👥 Top Users")
                users_resp = requests.get(f"{API_BASE}/admin/metrics/users?days={days}&limit=10", headers=headers, timeout=5)
                if users_resp.status_code == 200:
                    users_data = users_resp.json()["items"]
                    if users_data:
                        df = pd.DataFrame(users_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No user data available")
                else:
                    st.error(f"Error: {users_resp.status_code}")
            
            # Funnel analysis
            st.divider()
            st.subheader("🔄 Conversion Funnel")
            funnel_resp = requests.get(f"{API_BASE}/admin/metrics/funnel?days={days}", headers=headers, timeout=5)
            if funnel_resp.status_code == 200:
                funnel = funnel_resp.json()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Stage Users")
                    stages = funnel["stages_users"]
                    for stage, count in stages.items():
                        st.metric(stage.replace("_", " ").title(), count)
                
                with col2:
                    st.markdown("#### Conversion Rates")
                    conversions = funnel["conversions"]
                    for conv, rate in conversions.items():
                        st.metric(conv, f"{rate:.1%}")
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Could not connect to API: {e}")
            st.info("💡 Make sure your FastAPI server is running on http://127.0.0.1:8001")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    else:
        st.info("🔐 Please enter your admin key to view analytics")
    
    # Stop here - don't render the main app when showing admin dashboard
    st.stop()

else:
    # Render current step using extracted renderers
    render_current_step()

# Progress celebrations moved to sidebar to avoid scrolling issues
# Main content area stays clean and navigation-friendly

# ------------- Clean Sidebar -----------
with st.sidebar:
    # Header with app branding
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 1.5rem;">
    <h2 style="color: white; margin: 0; font-size: 1.3rem;">✨ AI Keyword Tool</h2>
    <p style="color: rgba(255,255,255,0.9); margin: 0.25rem 0 0 0; font-size: 0.85rem;">Smart SEO Content Strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Workflow navigation - essential for users
    st.markdown("### 🎯 Choose Workflow")
    current_workflow = st.session_state.get("selected_workflow", "keyword_research")
    
    workflows = [
        ("keyword_research", "🔍", "Keyword Research"),
        ("quick_brief", "⚡", "Quick Brief"),
        ("content_outline", "📋", "Content Outline"),
        ("content_ideas", "💡", "Content Ideas")
    ]
    
    for workflow_id, icon, title in workflows:
        is_selected = current_workflow == workflow_id
        
        if is_selected:
            # Selected workflow - highlighted
            st.button(f"{icon} {title}", 
                     key=f"selected_{workflow_id}",
                     disabled=True,
                     use_container_width=True,
                     type="primary")
        else:
            # Clickable workflow option
            if st.button(f"{icon} {title}", 
                        key=f"select_{workflow_id}",
                        use_container_width=True):
                st.session_state.selected_workflow = workflow_id
                # Reset workflow state when switching
                workflow_keys = ["ux_step", "selected_keyword", "brief_output", "serp_data", "keywords_data"]
                for key in workflow_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    st.divider()
    
    # Admin Dashboard
    if st.button("⚙️ Admin Dashboard", use_container_width=True, help="View analytics and admin features"):
        st.session_state.show_admin = True
        st.rerun()
    
    st.divider()
    
    # Current status with compact celebration
    current_step = st.session_state.get("ux_step", 1)
    selected_kw = st.session_state.get("selected_keyword", "")
    
    if selected_kw:
        st.success(f"🎯 **Target:** {selected_kw}")
        
        # Compact celebration for progress
        if current_step >= 3:
            st.caption("🎉 Great progress! Keep going!")
    elif current_workflow == "keyword_research":
        st.info(f"📍 **Step {current_step} of 5**")
        
        # Compact motivation
        if current_step == 1:
            st.caption("💡 Tell us about your business")
        elif current_step == 2:
            st.caption("🔍 Find your best keywords")
    else:
        st.info("📍 **Ready to start**")
    
    # Essential actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset", use_container_width=True, help="Reset current workflow"):
            workflow_keys = ["ux_step", "selected_keyword", "brief_output", "serp_data", "keywords_data"]
            for key in workflow_keys:
                if key in st.session_state:
                    del st.session_state[key]
            if current_workflow == "keyword_research":
                state_manager.go_to_step(1)
            st.rerun()
    
    with col2:
        if st.button("❓ Help", use_container_width=True, help="Get help"):
            if current_workflow == "keyword_research":
                state_manager.open_help(current_step)
            else:
                st.info("Help available for Keyword Research workflow")
    
    st.divider()
    
    # Recent work - simplified
    st.markdown("### 📚 Recent Sessions")
    
    try:
        from src.utils.db_utils import safe_get_recent_sessions
        recent_sessions = safe_get_recent_sessions(3)
        
        if recent_sessions:
            for session_id, topic, created_at in recent_sessions:
                display_topic = topic[:20] + "..." if len(topic) > 20 else topic
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(created_at.split('T')[0])
                    date_str = date_obj.strftime("%b %d")
                except:
                    date_str = "Recent"
                
                st.caption(f"📝 {display_topic} - {date_str}")
        else:
            st.caption("No recent sessions")
            
    except Exception:
        st.caption("History unavailable")
    
    st.divider()
    
    # Power user shortcuts  
    with st.expander("⚡ Power User Shortcuts"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Quick Demo", help="Load example data"):
                # Pre-fill with example business
                st.session_state.seed_input = "Digital marketing agency helping local restaurants get more customers through social media, Google ads, and review management"
                st.session_state.industry_input = "Digital Marketing"
                st.session_state.audience_input = "Local restaurants, food businesses"
                st.session_state.country_input = "US"
                st.session_state.selected_workflow = "keyword_research"
                st.session_state.ux_step = 2  # Skip to keywords
                st.success("🎯 Demo data loaded!")
                st.rerun()
                
        with col2:
            if st.button("💾 Export Data", help="Download your work"):
                # Quick export functionality
                current_data = {
                    "business": st.session_state.get("seed_input", ""),
                    "industry": st.session_state.get("industry_input", ""),
                    "audience": st.session_state.get("audience_input", ""),
                    "keyword": st.session_state.get("selected_keyword", ""),
                    "step": st.session_state.get("ux_step", 1)
                }
                st.json(current_data)
                
        # Keyboard shortcuts info
        st.caption("""
        💡 **Pro Tips:** 
        • Use Tab to navigate between fields quickly
        • Press Enter in text fields to auto-advance
        • Bookmark this page for quick access
        """)
    
    # Simple footer
    st.caption("🎯 AI-powered SEO content strategy")

