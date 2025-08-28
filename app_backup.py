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

# Initialize centralized state management
# This replaces all the individual session state initializations
state_manager._initialize_state()  # Ensure state is initialized when app runs

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

# Hero section with better visual hierarchy
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
if st.session_state.help_open:
    _help_dialog()
    # Reset the help_open state after showing dialog to prevent repeated popups
    st.session_state.help_open = False


def step_header():
    s = st.session_state.ux_step
    steps = [
        ("🧭", "Inputs", 1),
        ("🔎", "Keywords", 2),
        ("📝", "Brief", 3),
        ("🔍", "SERP", 4),
        ("💡", "Suggestions", 5),
    ]
    html = ['<div class="stepper">']
    for icon, label, num in steps:
        cls = "step"
        if s == num: cls += " step--active"
        elif s > num: cls += " step--done"
        html.append(f'<span class="{cls}"><span class="step__icon">{icon}</span>{label}</span>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)
    st.divider()

# Custom CSS for better reading width and spacing
st.markdown("""
<style>
section.main .block-container { max-width: 1000px; padding-top: 2rem; }

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

/* step chips - better contrast and visibility */
.stepper { display:flex; gap:.75rem; margin:1rem 0 1.5rem; }
.step { padding:.5rem .8rem; border-radius:8px; font-weight:600; font-size:14px;
        background:#f8fafc; border:2px solid #e2e8f0; color:#475569; transition: all 0.2s ease; }
.step--active { background:#3b82f6; border-color:#2563eb; color:#ffffff; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3); }
.step--done { background:#10b981; border-color:#059669; color:#ffffff; }
.step__icon { margin-right:.4rem; }
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

def get_keywords_json(prompt: str):
    """Legacy helper expected by tests. Uses chat.completions style mocked in tests.
    Returns parsed JSON content from first choice; propagates JSON errors.
    """
    if client is None:
        raise RuntimeError("OpenAI client not initialized")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
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

# Quick navigation link to A/B comparison page
try:
    st.sidebar.page_link("pages/2_📊_Compare_Runs.py", label="📊 Compare Runs")
except Exception:
    # Fallback (older Streamlit versions without page_link)
    pass

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

# Render current step using extracted renderers
render_current_step()

# ------------- Clean implementation - sidebar handled in step_renderers.py -----------
# Note: Sidebar is now rendered within step_renderers.py for better organization
    # Header with app branding
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin-bottom: 1.5rem;">
    <h2 style="color: white; margin: 0; font-size: 1.3rem;">✨ AI Keyword Tool</h2>
    <p style="color: rgba(255,255,255,0.9); margin: 0.25rem 0 0 0; font-size: 0.85rem;">Smart SEO Content Strategy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Current progress indicator
    current_step = st.session_state.get("ux_step", 1)
    selected_kw = st.session_state.get("selected_keyword", "")
    
    st.markdown("### 📍 Current Progress")
    
    # Progress visualization
    progress_steps = [
        ("🧭 Business Input", 1, "✅" if current_step > 1 else "📍" if current_step == 1 else "⏸️"),
        ("🔎 Keywords Found", 2, "✅" if current_step > 2 else "📍" if current_step == 2 else "⏸️"),
        ("📝 Brief Generated", 3, "✅" if current_step > 3 else "📍" if current_step == 3 else "⏸️"),
        ("🔍 SERP Analyzed", 4, "✅" if current_step > 4 else "📍" if current_step == 4 else "⏸️"),
        ("💡 Strategy Ready", 5, "✅" if current_step >= 5 else "📍" if current_step == 5 else "⏸️")
    ]
    
    for step_name, step_num, status in progress_steps:
        if status == "✅":
            st.markdown(f"<div style='color: #10b981; padding: 0.25rem 0;'>{status} {step_name}</div>", unsafe_allow_html=True)
        elif status == "📍":
            st.markdown(f"<div style='color: #3b82f6; padding: 0.25rem 0; font-weight: 600;'>{status} {step_name}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color: #9ca3af; padding: 0.25rem 0;'>{status} {step_name}</div>", unsafe_allow_html=True)
    
    if selected_kw:
        st.info(f"🎯 **Target:** {selected_kw}")
    
    st.divider()
    
    # Quick actions based on current step
    st.markdown("### ⚡ Quick Actions")
    
    if current_step == 1:
        st.markdown("📝 Fill out your business details to get started")
    elif current_step == 2:
        st.markdown("🔍 Review keywords and select the best opportunity")
    elif current_step == 3:
        st.markdown("📋 Generate your content brief with AI")
    elif current_step == 4:
        st.markdown("🔍 Analyze competitor search results")
    elif current_step == 5:
        st.markdown("💡 Get your final content strategy")
    
    # Quick navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Restart", use_container_width=True, help="Start a new keyword analysis"):
            for key in list(st.session_state.keys()):
                if key.startswith(("keywords_", "selected_", "brief_", "serp_", "ai_")):
                    del st.session_state[key]
            state_manager.go_to_step(1)
    
    with col2:
        if st.button("❓ Help", use_container_width=True, help="Get help for current step"):
            state_manager.open_help(current_step)
    
    # Export section for active sessions
    session_id = st.session_state.get("current_session_id")
    if session_id and current_step >= 3:  # Only show after brief is generated
        st.markdown("### 📄 Export Session")
        if st.button("📄 Export to Markdown", use_container_width=True, help="Export complete session as Markdown"):
            with st.spinner("Exporting session..."):
                try:
                    from src.utils.db_utils import safe_get_full_session_data
                    session_data = safe_get_full_session_data(session_id)
                    
                    if session_data and session_data.get("session"):
                        # Import export function with path handling
                        import sys
                        import os
                        base_dir = os.path.dirname(__file__)
                        ai_tool_dir = os.path.join(base_dir, 'ai-keyword-tool')
                        if ai_tool_dir not in sys.path:
                            sys.path.append(ai_tool_dir)
                        
                        from core.export import export_to_markdown
                        filepath = export_to_markdown(session_id, session_data)
                        
                        # Show success message
                        st.success("✅ Session exported!")
                        st.caption(f"📁 {os.path.basename(filepath)}")
                        
                        # Offer download
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        st.download_button(
                            "💾 Download",
                            data=content,
                            file_name=os.path.basename(filepath),
                            mime="text/markdown",
                            use_container_width=True
                        )
                    else:
                        st.error("❌ No session data found")
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
        
        st.divider()
    
    # A/B Testing link
    try:
        st.page_link("pages/2_📊_Compare_Runs.py", label="📊 Compare A/B Results", use_container_width=True)
    except Exception:
        pass
    
    st.divider()
    
    # Recent work section
    st.markdown("### 📚 Recent Work")
    
    try:
        from src.utils.db_utils import safe_get_recent_sessions
        recent_sessions = safe_get_recent_sessions(4)
        
        if recent_sessions:
            for session_id, topic, created_at in recent_sessions:
                # Format date nicely
                try:
                    date_str = created_at.split('T')[0] if 'T' in created_at else created_at[:10]
                    # Convert to more readable format
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(created_at.split('T')[0])
                    date_str = date_obj.strftime("%b %d")
                except:
                    date_str = "Recent"
                
                # Truncate topic for display
                display_topic = topic[:35] + "..." if len(topic) > 35 else topic
                
                # Create a card for each session
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 0.75rem; border-radius: 8px; border-left: 3px solid #3b82f6; margin: 0.5rem 0;">
                <div style="font-weight: 600; color: #1e293b; font-size: 0.9rem;">{display_topic}</div>
                <div style="color: #64748b; font-size: 0.75rem; margin-top: 0.25rem;">📅 {date_str}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 1rem; color: #64748b; font-style: italic;">
            No previous sessions yet.<br>
            Generate your first brief to see it here! 🚀
            </div>
            """, unsafe_allow_html=True)
            
    except Exception:
        st.caption("Session history unavailable")
    
    # Keep a simple in-memory history for this session
    if "history" not in st.session_state:
        st.session_state.history = []
    
    # Render cache info in sidebar if in dev mode
    cache_manager.render_cache_info()
    
    st.divider()
    
    # App info footer
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #64748b; font-size: 0.8rem;">
    <strong>🎯 AI Keyword Strategy Tool</strong><br>
    Smart keyword research + AI-powered content briefs<br>
    <span style="color: #9ca3af;">Powered by GPT-4o-mini</span>
    </div>
    """, unsafe_allow_html=True)

