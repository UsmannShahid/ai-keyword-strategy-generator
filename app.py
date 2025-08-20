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
from ui_helpers import render_copy_from_dataframe
from services import KeywordService, generate_writer_notes, generate_brief_with_variant, fetch_serp_snapshot
from parsing import SAFE_OUTPUT, parse_brief_output, detect_placeholders
from utils import slugify, default_report_name
from prompt_manager import prompt_manager
from scoring import add_scores, quickwin_breakdown, explain_quickwin
from eval_logger import log_eval
from brief_renderer import brief_to_markdown_full
from serp_utils import analyze_serp



# OpenAI SDK (current usage style)
# pip install --upgrade openai
from openai import OpenAI

# --- GLOBAL UX: hero + state ---
st.set_page_config(page_title="Keyword Quick Wins + AI Brief", page_icon="✨", layout="centered")

if "ux_step" not in st.session_state:
    st.session_state.ux_step = 1  # 1: Inputs, 2: Keywords, 3: Brief
if "selected_keyword" not in st.session_state:
    st.session_state.selected_keyword = None
if "variant" not in st.session_state:
    st.session_state.variant = "A"

# first-run onboarding flag
if "seen_help" not in st.session_state:
    st.session_state.seen_help = False
if "show_help" not in st.session_state:
    st.session_state.show_help = False

# --- Help state ---
if "help_open" not in st.session_state:
    st.session_state.help_open = False
if "help_step" not in st.session_state:
    st.session_state.help_step = 1

def _open_help(step: Optional[int] = None):
    if step is not None:
        st.session_state.help_step = step
    st.session_state.help_open = True

def _close_help():
    st.session_state.help_open = False

def _step_tip_popover(lines: List[str]):
    with st.popover("Need tips?"):
        for x in lines:
            st.markdown(f"- {x}")

def _render_notes_section(title: str, items, why: str | None = None):
    """Render a notes section with an optional 'why this matters' line."""
    items = [str(x).strip() for x in (items or []) if str(x).strip()]
    if not items and not why:
        return
    st.markdown(f"**{title}**")
    if why:
        st.caption(why)
    for it in items:
        st.markdown(f"- {it}")


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

# help content display
def show_help_modal():
    st.session_state.show_help = True

def render_help_content():
    if st.session_state.show_help:
        with st.container():
            st.markdown("---")
            st.markdown("### ✨ Quick-Win Keyword Finder + AI Content Brief")
            
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("✕ Close", key="close_help"):
                    st.session_state.show_help = False
                    st.rerun()
            
            st.write(
                "This tool helps you **find SEO opportunities** your competitors are missing — "
                "then turns them into a **ready-to-write content brief** for your writers or AI tools."
            )

            st.markdown("#### 🚀 Why this matters for SEO")
            st.write(
                "- **Find low-competition keywords**: Target search terms you can realistically rank for.\n"
                "- **Focus on intent**: Prioritize keywords with buyer or informational intent.\n"
                "- **Save research time**: Skip hours of manual SERP checks.\n"
                "- **Publish faster**: Give your writers a structured, optimized brief.\n"
                "- **Outperform rivals**: Identify outdated or weak top-ranking content and beat it."
            )

            st.markdown("#### 📌 How to use")
            st.write(
                "1. **Describe your niche** or enter a seed keyword.\n"
                "2. Review the generated **Quick-Win keywords**.\n"
                "3. Pick one → **Generate a content brief** instantly.\n"
                "4. Export as Markdown or copy-paste into your CMS."
            )

            st.markdown("#### 📄 What's in a content brief?")
            st.write(
                "- SEO-friendly title & meta description\n"
                "- H2/H3 outline with suggested word count\n"
                "- Related keywords and entities\n"
                "- Internal and external link ideas\n"
                "- FAQs to capture extra search queries"
            )

            st.markdown("> **Tip:** Use this tool alongside Google Search Console or competitor analysis to target missed opportunities.")
            
            if st.button("Got it", type="primary", key="got_it_help"):
                st.session_state.seen_help = True
                st.session_state.show_help = False
                st.rerun()
            st.markdown("---")

# Helper functions for navigation
def _go(step: int):
    st.session_state.ux_step = step

def _on_keyword_pick():
    pick = st.session_state.get("kw_pick_select")
    if pick:
        st.session_state.selected_keyword = pick
        _go(3)
        st.toast(f"Keyword selected: {pick}")
        st.rerun()

# SVG Icons
ICON_BRIEF = """<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"
  xmlns="http://www.w3.org/2000/svg" style="vertical-align:-2px;">
  <path d="M8 4h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zM8 6v12h8V6H8zm2 2h4v1H10V8zm0 3h4v1H10v-1zm0 3h2v1H10v-1z"/></svg>"""

st.markdown("""
### ✨ Quick‑Win Keyword Finder + AI Content Brief
Find low‑competition, high‑intent keywords fast — then generate a clean, writer‑ready brief in one click.
""")

# header bar: Help button on the right
cols = st.columns([1,1,1,1,1])
with cols[-1]:
    if st.button("❓ Help"):
        _open_help(st.session_state.ux_step)

# Render dialog if flagged
if st.session_state.help_open:
    _help_dialog()

# render help content if requested (legacy system)
render_help_content()

def step_header():
    s = st.session_state.ux_step
    steps = [
        ("🧭", "Inputs", 1),
        ("🔎", "Keywords", 2),
        ("📝", "Content Brief", 3),
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
section.main .block-container { max-width: 980px; }

/* nicer heading spacing */
h2 { margin-top: 1.1rem !important; }
h3 { margin-top: .9rem !important; }

/* keyword/intents badges */
.k-badge { display:inline-block; padding:2px 8px; border-radius:16px; font-weight:600; font-size:12px; }
.k-badge--buy { background:#e6ffed; color:#09633b; }
.k-badge--info { background:#eef2ff; color:#3730a3; }
.k-badge--brand { background:#fef3c7; color:#92400e; }
.k-badge--weak { background:#fee2e2; color:#dc2626; }
.k-badge--strong { background:#d1fae5; color:#059669; }

/* step chips */
.stepper { display:flex; gap:.5rem; margin:.5rem 0 1rem; }
.step { padding:.35rem .6rem; border-radius:999px; font-weight:600;
        background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); }
.step--active { background:rgba(59,130,246,.15); border-color:rgba(59,130,246,.35); color:#93c5fd; }
.step--done { background:rgba(16,185,129,.15); border-color:rgba(16,185,129,.35); color:#6ee7b7; }
.step__icon { margin-right:.35rem; }
</style>
""", unsafe_allow_html=True)

# Color styling for intent categories
INTENT_COLORS = {
    "transactional": "#d1fae5",  # green-ish
    "informational": "#dbeafe",  # blue-ish
    "navigational":  "#fde68a",  # amber-ish
    "branded":       "#fce7f3",  # pink-ish
}


def style_intent(s: pd.Series):
    return [f"background-color: {INTENT_COLORS.get(v.lower(), '#f3f4f6')}" for v in s]

def render_intent_badge(intent: str) -> str:
    """Render an intent badge using CSS classes"""
    cls = "k-badge--buy" if "trans" in intent.lower() or "buyer" in intent.lower() else ("k-badge--info" if "info" in intent.lower() else "k-badge--brand")
    return f'<span class="k-badge {cls}">{intent}</span>'

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
if not OPENAI_API_KEY.startswith("sk-"):
    st.error("⚠️ API key format appears incorrect. OpenAI keys start with 'sk-'")
    st.stop()

st.title("🔍 AI Keyword Strategy Generator")

# Quick navigation link to A/B comparison page
try:
    st.sidebar.page_link("pages/2_📊_Compare_Runs.py", label="📊 Compare Runs")
except Exception:
    # Fallback (older Streamlit versions without page_link)
    pass

# Keep a simple in-memory history for this session
if "history" not in st.session_state:
    st.session_state.history = []

# Initialize the keyword service
if "keyword_service" not in st.session_state:
    try:
        st.session_state.keyword_service = KeywordService()
    except Exception as e:
        st.error(f"❌ Failed to initialize keyword service: {e}")
        st.info("📝 Check your OpenAI API key in the .env file")
        st.stop()

# ------------- Small Utilities -------------------
def slugify(text: str) -> str:
    """Create a simple filename-friendly slug from a string."""
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in text.strip())[:60].strip("-")

def default_report_name(business_desc: str) -> str:
    """Generate a default report name from business description."""
    if not business_desc.strip():
        return "keyword-report"
    
    # Take first few words and slugify
    words = business_desc.strip().split()[:3]
    name = " ".join(words)
    return slugify(name) or "keyword-report"

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

def render_step_1():
    st.subheader("🧭 Step 1 — Tell us your niche")
    _step_tip_popover([
        "Start broad; refine with filters in Step 2.",
        "Set country/language for localized SERPs.",
    ])
    st.caption("Pro tip: Start broad (e.g., 'ergonomic chair') — we'll narrow with Quick‑Win filters.")
    
    # Business description input
    business_desc = st.text_input("Describe your website or business:", 
                                  value=st.session_state.get("business_desc", ""),
                                  placeholder="e.g., ergonomic office chairs for remote workers")
    
    # Additional context inputs
    col1, col2, col3 = st.columns(3)
    with col1:
        industry = st.text_input("Industry (optional)", 
                                value=st.session_state.get("industry", ""),
                                placeholder="e.g., furniture, SaaS")
    with col2:
        audience = st.text_input("Target audience (optional)", 
                                value=st.session_state.get("audience", ""),
                                placeholder="e.g., remote workers")
    with col3:
        location = st.text_input("Location/Market (optional)", 
                                value=st.session_state.get("location", ""),
                                placeholder="e.g., US, Canada")
    
    # Prompt strategy selection
    st.markdown("#### 🎯 Keyword Strategy")
    prompt_options = prompt_manager.get_prompt_display_names()
    available_prompts = list(prompt_options.keys())
    
    if available_prompts:
        # Load display names from PromptManager
        disp_map = prompt_manager.get_prompt_display_names()  # {key: "Pretty Label"}
        inv_map = {v: k for k, v in disp_map.items()}  # reverse map

        available_prompts = list(disp_map.keys())

        if available_prompts:
            # Figure out what to show as default in the dropdown
            current_key = st.session_state.get("selected_prompt", "default_seo")
            current_label = disp_map.get(current_key, next(iter(disp_map.values())))

            selected_prompt_display = st.selectbox(
                "Choose your keyword research approach:",
                options=list(disp_map.values()),
                index=list(disp_map.values()).index(current_label) if current_label in disp_map.values() else 0,
            )

            # Store the actual key in session_state
            selected_prompt = inv_map[selected_prompt_display]
            st.session_state["selected_prompt"] = selected_prompt

            # Show helper caption under dropdown
            help_lines = {
                "🎯 Balanced SEO Strategy": "Good default. Mix of volume + intent.",
                "🔍 Competitive Analysis": "Look at rivals to find missed gaps.",
                "🌱 Long-Tail Keywords (Low Volume, High Intent)": "Lower volume but easier wins and clearer intent.",
                "📈 Trending Searches": "Timely topics with rising interest.",
            }
            st.caption(help_lines.get(selected_prompt_display, "Pick a style that fits your niche."))

        else:
            selected_prompt = "default_seo"
            st.info("💡 Using default SEO strategy (prompt files not found)")
    
    # Save inputs to session state
    st.session_state.business_desc = business_desc
    st.session_state.industry = industry
    st.session_state.audience = audience
    st.session_state.location = location
    st.session_state.selected_prompt = selected_prompt
    
    st.caption("💡 Tip: The more specific your description, the better the keyword suggestions.")
    
    st.divider()
    disabled = not bool(business_desc.strip())
    if st.button("Next: Find Keywords →", type="primary", disabled=disabled):
        st.session_state.ux_step = 2
        st.rerun()

def render_step_2():
    st.subheader("🔎 Step 2 — Quick-Win Keywords")
    _step_tip_popover([
        "Raise Min score to focus on wins.",
        "Use Include/Exclude to stay on-topic.",
    ])
    st.caption("Sort by score and volume. Pick a high-intent keyword to generate a brief.")
    
    # Show the business context
    business_desc = st.session_state.get("business_desc", "")
    st.info(f"🎯 **Finding keywords for:** {business_desc}")
    
    # Generate keywords if not already done or if inputs changed
    if "generated_df" not in st.session_state or st.button("🔄 Regenerate Keywords"):
        with st.spinner("Generating keywords..."):
            try:
                # Use the keyword service to generate keywords
                data = st.session_state.keyword_service.generate_keywords(
                    business_desc=st.session_state.get("business_desc", ""),
                    industry=st.session_state.get("industry", ""),
                    audience=st.session_state.get("audience", ""),
                    location=st.session_state.get("location", ""),
                    prompt_template=st.session_state.get("selected_prompt", "default_seo")
                )
                
                # Build table from parsed data
                df = to_dataframe(data)
                
                # Add scoring and priority - rename columns to match expected format
                df = add_scores(df, intent_col="category", kw_col="keyword")
                df = df.rename(columns={
                    "keyword": "Keyword",
                    "category": "Intent", 
                    "opportunity": "QW Score"
                })
                # Add Volume column (placeholder for now)
                df["Volume"] = pd.Series([1000, 800, 600, 400, 300] * (len(df) // 5 + 1))[:len(df)]
                
                if not df.empty:
                    df = df.sort_values(["priority"], ascending=True).reset_index(drop=True)
                    st.session_state.generated_df = df
                    st.success(f"Generated {len(df)} keywords!")
                    
                    # Save to history for sidebar
                    if "history" not in st.session_state:
                        st.session_state.history = []
                    today = datetime.now().strftime("%Y-%m-%d")
                    st.session_state.history.append({
                        "business": st.session_state.get("business_desc", ""),
                        "industry": st.session_state.get("industry", ""),
                        "audience": st.session_state.get("audience", ""),
                        "location": st.session_state.get("location", ""),
                        "count": len(df),
                        "ts": today,
                    })
                else:
                    st.warning("No keywords generated. Try adjusting your description.")
                    return
                    
            except Exception as e:
                st.error(f"Error generating keywords: {e}")
                return
    
    # Display keywords table with enhanced styling and filters
    if "generated_df" in st.session_state:
        df = st.session_state.generated_df
        
        if df is None or df.empty:
            st.info("No keywords found. Try regenerating or going back to adjust inputs.")
            if st.button("← Back"):
                st.session_state.ux_step = 1
                st.rerun()
            return

        # Normalize types
        df = df.copy()
        if "QW Score" in df.columns:
            df["QW Score"] = pd.to_numeric(df["QW Score"], errors="coerce").fillna(0).clip(0,100)
        if "Volume" in df.columns:
            df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)

        # Quick filters
        with st.expander("🔍 Filters", expanded=True):
            c1, c2, c3 = st.columns([1,1,1])
            min_score = c1.slider("Min Quick-Win score", 0, 100, 60)
            include = c2.text_input("Include terms", value="", placeholder="comma-separated (optional)")
            exclude = c3.text_input("Exclude terms", value="", placeholder="comma-separated (optional)")

        filt = (df["QW Score"] >= min_score)
        if include.strip():
            inc_terms = [t.strip().lower() for t in include.split(",") if t.strip()]
            for t in inc_terms:
                filt &= df["Keyword"].str.lower().str.contains(t, na=False)
        if exclude.strip():
            exc_terms = [t.strip().lower() for t in exclude.split(",") if t.strip()]
            for t in exc_terms:
                filt &= ~df["Keyword"].str.lower().str.contains(t, na=False)
        fdf = df.loc[filt].reset_index(drop=True)

        if fdf.empty:
            st.warning("No rows after filters.")
            if st.button("← Back"):
                st.session_state.ux_step = 1
                st.rerun()
            return

        # Ensure there is a default pick (top by score, then volume)
        if not st.session_state.get("kw_pick_select") and not fdf.empty:
            top_row = fdf.sort_values(["QW Score", "Volume"], ascending=False).iloc[0]
            st.session_state.kw_pick_select = top_row["Keyword"]
            st.session_state.selected_keyword = st.session_state.kw_pick_select  # keep in sync
        # ---- Enhanced Styler: color QW Score, volume bars, intent badges ----
        def style_df(_df: pd.DataFrame):
            sty = _df.style

            if "QW Score" in _df.columns:
                def score_color(val):
                    try:
                        score = float(val)
                        if score >= 80:
                            return "background-color:#dcfce7;color:#166534"
                        elif score >= 60:
                            return "background-color:#fef3c7;color:#92400e"
                        else:
                            return "background-color:#fee2e2;color:#991b1b"
                    except:
                        return ""
                sty = sty.map(score_color, subset=["QW Score"])

            if "Intent" in _df.columns:
                def intent_color(val):
                    v = str(val).lower()
                    if "transaction" in v or "buyer" in v:
                        return "background-color:#e6ffed;color:#09633b;border-radius:16px;padding:2px 8px; font-weight:600"
                    if "inform" in v:
                        return "background-color:#eef2ff;color:#3730a3;border-radius:16px;padding:2px 8px; font-weight:600"
                    if "navig" in v or "branded" in v:
                        return "background-color:#fef3c7;color:#92400e;border-radius:16px;padding:2px 8px; font-weight:600"
                    return ""
                sty = sty.map(intent_color, subset=["Intent"])
            return sty

        show_cols = [c for c in ["Keyword","QW Score","Intent","Volume","Notes"] if c in fdf.columns]
        st.markdown("### 📊 Keyword Results")
        st.dataframe(
            style_df(fdf[show_cols]), 
            use_container_width=True, 
            height=min(600, 48 + 33*min(len(fdf), 12))
        )
        
        # Quick wins section
        top_n = 5
        quick_wins = fdf.sort_values(["QW Score"], ascending=False).head(top_n)
        
        with st.expander(f"⚡ Top {top_n} Quick Wins", expanded=True):
            st.caption(f"Highest scoring keywords for immediate content opportunities")
            
            for idx, row in quick_wins.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    intent_badge = render_intent_badge(row['Intent'])
                    st.markdown(f"**{row['Keyword']}** {intent_badge}", unsafe_allow_html=True)
                    st.caption(f"Volume: {row.get('Volume', 'N/A')} | Score: {row['QW Score']:.0f}")
                with col2:
                    pass
                with col3:
                    if st.button(f"📝 Brief This", key=f"brief_{idx}_{row['Keyword'][:20]}"):
                        st.session_state.selected_keyword = row['Keyword'] 
                        st.session_state.ux_step = 3
                        st.rerun()

        # Selection control
        st.markdown("#### Pick a keyword to brief")
        pick = st.selectbox(
            "Keyword",
            options=fdf["Keyword"].tolist(),
            index=0,
            key="kw_pick_select",
            label_visibility="collapsed",
            on_change=_on_keyword_pick,
        )

        # Keep selected_keyword in sync even if user doesn't change the selectbox
        if pick and st.session_state.get("selected_keyword") != pick:
            st.session_state.selected_keyword = pick

        if pick:
            st.success(f"✅ Selected: **{pick}**")

            # 👉 Explain Quick-Win Score popover
            try:
                row = fdf.loc[fdf["Keyword"] == pick].iloc[0].to_dict()
                bd = quickwin_breakdown(row)
                with st.popover("🔍 Explain this score"):
                    st.markdown(f"**Quick-Win Score:** {bd['score']}")
                    st.markdown(f"- Volume: **{bd['volume']}**/mo")
                    st.markdown(f"- Intent: **{bd['intent']}**")
                    subs = bd["subscores"]
                    st.markdown(f"- Subscores → volume={int(subs['volume_score'])}, intent_boost={subs['intent_boost']}, serp_weakness={subs['serp_weakness']}")
                    st.divider()
                    st.write(explain_quickwin(bd))
            except Exception as e:
                st.warning(f"Could not explain score: {e}")
    
    st.divider()
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("← Back to Inputs"):
            st.session_state.ux_step = 1
            st.rerun()
    with col2:
        disabled = not (st.session_state.get("selected_keyword") or st.session_state.get("kw_pick_select"))
        if st.button("Next: Generate Brief →", type="primary", disabled=disabled):
            st.session_state.ux_step = 3
            st.rerun()


def render_step_3():
    st.subheader("📝 Step 3 — AI Content Brief")
    _step_tip_popover([
        "Variant A = structure, Variant B = tone.",
        "Download as Markdown and share.",
    ])
    st.caption("Choose a prompt variant (A/B) for structure vs. tone. Download as Markdown for writers.")
    
    keyword = st.session_state.get("selected_keyword")
    if not keyword:
        st.error("No keyword selected. Please go back to Step 2.")
        return
    
    st.info(f"📝 **Generating brief for:** {keyword}")
    
    # SERP Snapshot
    country = st.session_state.get("country", "US")
    language = st.session_state.get("language", "en")

    with st.expander("🔍 SERP Snapshot (top 5)", expanded=True):
        with st.spinner("Fetching SERP…"):
            try:
                serp_raw = fetch_serp_snapshot(keyword or "", country, language) if keyword else []
            except Exception as e:
                st.warning(f"Could not fetch SERP data: {e}")
                serp_raw = []
        serp = analyze_serp(serp_raw)
        s = serp["summary"]
        
        # Store SERP data in session state for logging
        st.session_state.serp_data = serp
        st.session_state.show_serp = True
        
        st.caption(f"Weak spots: {s['weak_any']} (forums: {s['weak_forum']}, thin: {s['weak_thin']}, old: {s['weak_old']})")

        for i, r in enumerate(serp["rows"], 1):
            tags = []
            if r["weak_forum"]: tags.append("forum")
            if r["weak_thin"]:  tags.append("thin")
            if r["weak_old"]:   tags.append("old")
            tag = " · ".join(tags) if tags else "—"
            st.markdown(
                f"**{i}. {r.get('title','(no title)')}**  \n"
                f"<span style='color:gray'>{r.get('domain','')}</span> • weak: <span style='color:#f59e0b'>{tag}</span>  \n"
                f"{(r.get('snippet') or '')[:220]}",
                unsafe_allow_html=True
            )

    # Variant picker (contextual to this step)
    variants = prompt_manager.get_variants("content_brief") or ["A","B"]
    st.session_state.variant = st.selectbox(
        "Prompt Variant (A/B Testing)", 
        variants, 
        index=variants.index(st.session_state.variant) if st.session_state.variant in variants else 0,
        help="Different prompt strategies for content brief generation"
    )
    
    # Display selected keyword (read-only)
    st.text_input("Selected Keyword", value=keyword, disabled=True)
    
    # Generate brief button
    if st.button("🚀 Generate Content Brief", type="primary"):
        with st.spinner("Generating content brief..."):
            try:
                output, prompt_used, latency_ms, usage = generate_brief_with_variant(
                    keyword=keyword,
                    variant=st.session_state.variant
                )
                
                # Store results in session state
                st.session_state.brief_output = output
                st.session_state.brief_prompt = prompt_used
                st.session_state.brief_latency = latency_ms
                st.session_state.brief_usage = usage
                
            except Exception as e:
                st.error(f"Error generating brief: {e}")
                return
    
    # Display generated brief
        
    if "brief_output" in st.session_state:
        output = st.session_state.brief_output
        data, is_json = parse_brief_output(output)
        
        st.markdown("---")
        
        # --- Render result (modern tabs) ---
        st.subheader("📝 AI Content Brief")

        # you should already have: data, is_json, keyword
        # ensure we have notes + serp summary from session if available
        writer_notes = st.session_state.get("writer_notes_last")
        serp_summary = (st.session_state.get("serp_data") or {}).get("summary")

        # if you don't have SERP in session yet, compute a quick snapshot summary on the fly (safe fallback)
        if not serp_summary and keyword:
            try:
                country = st.session_state.get("country", "US")
                language = st.session_state.get("language", "en")
                serp_raw = fetch_serp_snapshot(keyword, country, language)
                serp = analyze_serp(serp_raw)
                st.session_state["serp_data"] = serp
                serp_summary = serp.get("summary")
            except Exception:
                serp_summary = None

        if is_json:
            # build full, writer-ready doc (brief + optional notes + serp summary)
            md = brief_to_markdown_full(data, writer_notes=writer_notes, serp_summary=serp_summary)

            # --- TABS LAYOUT ---
            tab_labels = ["📄 Content Brief", "🧠 Writer’s Notes", "🔍 SERP Snapshot"]

            # Only add Debug tab if dev_mode is enabled
            if st.session_state.get("dev_mode", False):
                tab_labels.append("⚙️ Debug (Advanced)")

            tabs = st.tabs(tab_labels)
            tab_brief, tab_notes, tab_serp, *tab_debug = tabs

            # Content Brief tab
            with tab_brief:
                st.markdown(md)
                st.download_button(
                    "⬇️ Download Brief (Markdown)",
                    data=md.encode("utf-8"),
                    file_name=f"{(keyword or 'content-brief').replace(' ', '-') }__{st.session_state.variant}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            # Writer's Notes tab (generate if missing)
            # Writer's Notes tab (generate if missing)
            with tab_notes:
                st.caption("Add practical guidance for a writer: audience, angle, sections, citations.")

                # ✅ Friendly labels instead of A/B, mapped back internally
                variant_label_map = {
                    "✍️ Concise Notes (Quick Checklist)": "A",
                    "📖 Detailed Notes (Step-by-Step)": "B",
                }
                wn_variant_label = st.selectbox(
                    "✍️ Note Style",
                    list(variant_label_map.keys()),
                    index=0,
                    key="wn_variant_tab",
                    help="Choose how detailed you want the writing guidance to be."
                )
                wn_variant = variant_label_map[wn_variant_label]

                # Tiny explainer popover
                with st.popover("What’s this?"):
                    st.markdown(
                        "**Concise:** quick checklist to speed drafting.\n\n"
                        "**Detailed:** step-by-step guidance with more examples and sections."
                    )

                if writer_notes:
                    # Header trio
                    st.markdown("**Audience:** " + str(writer_notes.get("target_audience", "—")))
                    st.markdown("**Intent:** " + str(writer_notes.get("search_intent", "—")))
                    st.markdown("**Primary angle:** " + str(writer_notes.get("primary_angle", "—")))

                    # ✅ Clear “why this matters” per section
                    why_map = {
                        "Writer notes": "Practical guidance for how to structure and write the article.",
                        "Must-cover sections": "Essential H2/H3s to satisfy search intent and cover the topic fully.",
                        "Entity gaps": "Topics or terms competitors forgot — covering these helps you win.",
                        "Data freshness": "Keeps your article up-to-date; cite 2024–2025 sources where possible.",
                        "Internal link targets": "Pages on your site to link to for SEO and user flow.",
                        "External citations needed": "Authoritative sources to build trust and E‑E‑A‑T.",
                        "Formatting enhancements": "Layouts (tables, checklists, schema) that improve readability and rankings.",
                        "Tone & style": "How the article should sound to match your brand and audience.",
                        "CTA ideas": "Prompts that nudge readers to the next step (signup, compare, contact).",
                        "Risk flags": "YMYL/legal/medical caveats to keep content safe and compliant.",
                    }

                    _render_notes_section("Writer notes", writer_notes.get("writer_notes"), why_map["Writer notes"])
                    _render_notes_section("Must-cover sections", writer_notes.get("must_cover_sections"), why_map["Must-cover sections"])
                    _render_notes_section("Entity gaps", writer_notes.get("entity_gaps"), why_map["Entity gaps"])
                    _render_notes_section("Data freshness", writer_notes.get("data_freshness"), why_map["Data freshness"])
                    _render_notes_section("Internal link targets", writer_notes.get("internal_link_targets"), why_map["Internal link targets"])
                    _render_notes_section("External citations needed", writer_notes.get("external_citations_needed"), why_map["External citations needed"])
                    _render_notes_section("Formatting enhancements", writer_notes.get("formatting_enhancements"), why_map["Formatting enhancements"])
                    _render_notes_section("Tone & style", writer_notes.get("tone_style"), why_map["Tone & style"])
                    _render_notes_section("CTA ideas", writer_notes.get("cta_ideas"), why_map["CTA ideas"])
                    _render_notes_section("Risk flags", writer_notes.get("risk_flags"), why_map["Risk flags"])

                    if rc := writer_notes.get("recommended_word_count"):
                        st.markdown(f"**Recommended word count:** {rc}")

                    # Download notes-only (still uses mapped A/B internally for filename)
                    notes_md = "## Writer's Notes\n" + "\n".join(
                        f"- {x}" for x in (writer_notes.get("writer_notes") or [])
                    )
                    st.download_button(
                        "⬇️ Download Writer's Notes (Markdown)",
                        data=notes_md.encode("utf-8"),
                        file_name=f"{(keyword or 'notes').replace(' ','-')}__notes_{wn_variant}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

                else:
                    # Generate inline if not present
                    if st.button("Generate Writer's Notes", type="primary", use_container_width=True, disabled=not keyword):
                        with st.spinner("Creating notes…"):
                            notes, ok, prompt_used, usage = generate_writer_notes(
                                keyword=keyword,
                                brief_dict=data,
                                serp_summary=serp_summary,
                                variant=wn_variant,  # mapped "A"/"B"
                            )
                        if ok:
                            st.session_state["writer_notes_last"] = notes
                            st.success("Writer's Notes added to this brief.")
                            st.rerun()
                        else:
                            st.warning("Model did not return valid JSON. Showing raw:")
                            st.code(notes.get("raw", ""), language="json")


            # SERP Snapshot tab
            with tab_serp:
                st.caption("Top results and weak-spot flags help you judge if you can win the SERP.")
                serp_data = st.session_state.get("serp_data")
                if not serp_data:
                    st.info("No SERP data yet.")
                else:
                    s = serp_data.get("summary", {})
                    st.markdown(
                        f"**Weak spots:** {s.get('weak_any',0)} "
                        f"(forums: {s.get('weak_forum',0)}, thin: {s.get('weak_thin',0)}, old: {s.get('weak_old',0)})"
                    )
                    # list rows if available
                    for i, r in enumerate(serp_data.get("rows", [])[:5], 1):
                        tags = []
                        if r.get("weak_forum"): tags.append("forum")
                        if r.get("weak_thin"):  tags.append("thin")
                        if r.get("weak_old"):   tags.append("old")
                        tag = " · ".join(tags) if tags else "—"
                        st.markdown(
                            f"**{i}. {r.get('title','(no title)')}**  \n"
                            f"<span style='color:gray'>{r.get('domain','')}</span> • weak: <span style='color:#f59e0b'>{tag}</span>  \n"
                            f"{(r.get('snippet') or '')[:220]}",
                            unsafe_allow_html=True
                        )
                    # refresh SERP
                    colr1, colr2 = st.columns([1,1])
                    if colr1.button("🔄 Refresh SERP"):
                        with st.spinner("Fetching SERP…"):
                            country = st.session_state.get("country", "US")
                            language = st.session_state.get("language", "en")
                            serp_raw = fetch_serp_snapshot(keyword, country, language)
                            serp = analyze_serp(serp_raw)
                            st.session_state["serp_data"] = serp
                        st.rerun()

            # Debug tab
            if st.session_state.get("dev_mode", False) and len(tabs) > 3:
                with tabs[-1]:
                    st.caption("⚙️ Raw AI output for troubleshooting (dev use only).")
                    st.json(data if is_json else {"raw": output})

        else:
            # Fallback: show raw output if not JSON
            st.warning("Model returned non-JSON output. Showing raw below:")
            st.markdown(output or "_No output_")

        # Feedback section
        st.markdown("---")
        st.markdown("### 💭 How was this brief?")
        rating = st.slider("Rating (1=poor, 5=excellent)", min_value=1, max_value=5, value=4)
        notes = st.text_area("Optional feedback (what was good/bad?)", placeholder="e.g., missing competitor analysis, great structure...")

        # Button to save feedback
        if st.button("💾 Save Feedback"):
            # --- Safe pulls from session ---
            brief_prompt   = st.session_state.get("brief_prompt", "")
            brief_latency  = float(st.session_state.get("brief_latency", 0) or 0)
            brief_usage    = st.session_state.get("brief_usage") or {}
            tokens_prompt  = brief_usage.get("prompt_tokens")
            tokens_comp    = brief_usage.get("completion_tokens")

            # Optional quality signals
            checklist      = st.session_state.get("quality_checklist")   # dict or None
            auto_flags     = st.session_state.get("brief_auto_flags")    # list or None
            is_json        = st.session_state.get("brief_is_json")       # bool or None

            # SERP summary if available
            serp_summary = None
            if st.session_state.get("show_serp") and keyword:
                serp_state = st.session_state.get("serp_data") or {}
                serp_summary = serp_state.get("summary")

            # 👉 NEW: Quick-Win breakdown for the selected keyword (if we can find the row)
            qw_breakdown = None
            qw_expl      = None
            try:
                df_all = st.session_state.get("generated_df")
                sel_kw = st.session_state.get("selected_keyword") or st.session_state.get("kw_pick_select")
                if df_all is not None and sel_kw:
                    # locate the row by keyword (case-insensitive, safe)
                    row_match = df_all.loc[df_all["Keyword"].str.lower() == str(sel_kw).lower()]
                    if not row_match.empty:
                        bd = quickwin_breakdown(row_match.iloc[0].to_dict())
                        qw_breakdown = bd
                        qw_expl = explain_quickwin(bd)
            except Exception as e:
                # don't fail logging if breakdown fails
                qw_breakdown = {"error": str(e)}
                qw_expl = None

            # Build extra payload
            extra_payload = {
                "app_version": "beta-mvp",
                "type": "content_brief",
                "is_json": bool(is_json) if is_json is not None else None,
                "auto_flags": auto_flags or [],
                "checklist": checklist or {},
                "serp_summary": serp_summary,
                "quickwin_breakdown": qw_breakdown,
                "quickwin_explanation": qw_expl,
                "output_chars": len(output or ""),
            }

            # Log the evaluation
            log_eval(
                variant=st.session_state.variant,
                keyword=keyword or "",
                prompt=brief_prompt,
                output=output or "",
                latency_ms=brief_latency,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_comp,
                user_rating=rating,
                user_notes=notes,
                extra=extra_payload,
            )

            st.success("✅ Feedback saved! This helps improve the AI prompts.")
            st.toast("Saved to evals.jsonl")

    # Navigation buttons
    st.divider()
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("← Back to Keywords"):
            st.session_state.ux_step = 2
            st.rerun()
    with col2:
        if st.button("🔄 Start Over"):
            # Reset session state
            for key in ["ux_step", "selected_keyword", "generated_df", "brief_output", "brief_prompt", "brief_latency", "brief_usage"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.ux_step = 1
            st.rerun()

# ------------- MAIN WIZARD FLOW ------------------------

# Display step header
step_header()

# Render current step
if st.session_state.ux_step == 1:
    render_step_1()
elif st.session_state.ux_step == 2:
    render_step_2()
elif st.session_state.ux_step == 3:
    render_step_3()

# ------------- Sidebar: Help + Navigation -----------
st.sidebar.title("📊 Quick Navigation")

# Quick navigation to Compare Runs page
try:
    st.sidebar.page_link("pages/2_📊_Compare_Runs.py", label="📊 Compare A/B Results")
except Exception:
    # Fallback for older Streamlit versions
    pass

st.sidebar.title("How to Use")
st.sidebar.markdown("""
**Step 1:** Describe your business and target market  
**Step 2:** Review generated keywords and pick one  
**Step 3:** Generate a comprehensive content brief  

💡 **Tip:** Be specific in your business description for better keywords.
""")

# Keep a simple in-memory history for this session
if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.title("Recent Sessions")
if st.session_state.history:
    for item in st.session_state.history[-3:][::-1]:
        st.sidebar.write(
            f"- **{item['business'][:25]}...** · {item['count']} kws"
        )
else:
    st.sidebar.caption("No sessions yet")

st.sidebar.title("About")
st.sidebar.markdown("""
🎯 **AI Keyword Strategy Tool**  
Find high-opportunity keywords and generate writer-ready content briefs.

Built with Streamlit + OpenAI GPT-4o-mini
""")

