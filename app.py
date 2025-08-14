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
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from ui_helpers import render_copy_from_dataframe
from services import KeywordService, generate_brief_with_variant
from parsing import SAFE_OUTPUT, parse_brief_output, detect_placeholders
from utils import slugify, default_report_name
from prompt_manager import prompt_manager
from scoring import add_scores
from eval_logger import log_eval
from brief_renderer import brief_to_markdown
from parsing import parse_brief_output


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

st.markdown("""
### ✨ Quick‑Win Keyword Finder + AI Content Brief
Find low‑competition, high‑intent keywords fast — then generate a clean, writer‑ready brief in one click.
""")

def step_header():
    s = st.session_state.ux_step
    steps = [
        ("1️⃣ Inputs", 1),
        ("2️⃣ Keywords", 2),
        ("3️⃣ Content Brief", 3),
    ]
    cols = st.columns(len(steps))
    for i, (label, num) in enumerate(steps):
        with cols[i]:
            if s == num:
                st.markdown(f"**{label}**")
            elif s > num:
                st.markdown(f"✅ {label}")
            else:
                st.markdown(f"⬜ {label}")
    st.divider()

# Custom CSS for better reading width and spacing
st.markdown("""
<style>
section.main .block-container { max-width: 900px; }
h2, h3 { margin-top: 1.1rem !important; }
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

st.set_page_config(page_title="AI Keyword Tool", page_icon="🔍", layout="centered")
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
    st.subheader("Step 1 — Tell us your niche")
    
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
        selected_prompt_display = st.selectbox(
            "Choose your keyword research approach:",
            options=[prompt_options[key] for key in available_prompts],
            index=0
        )
        # Get the actual prompt key from the display name
        selected_prompt = next(key for key, display in prompt_options.items() if display == selected_prompt_display)
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
    st.subheader("Step 2 — Quick‑Win Keywords")
    
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
                
                # Add scoring and priority
                df = add_scores(df, intent_col="category", kw_col="keyword")
                
                if not df.empty:
                    df = df.sort_values(["priority"]).reset_index(drop=True)
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
    
    # Display keywords table
    if "generated_df" in st.session_state:
        df = st.session_state.generated_df
        
        st.markdown("### 🗂️ Generated Keywords")
        styled = (
            df[["priority","keyword","category","opportunity"]]
              .style.apply(style_intent, subset=["category"])
        )
        st.dataframe(styled, use_container_width=True)
        
        # Quick wins section
        top_n = 10
        quick_wins = df.sort_values(["opportunity","keyword"], ascending=[False, True]).head(top_n)
        
        with st.expander(f"⚡ Top {top_n} Quick Wins", expanded=True):
            quick_wins_styled = (
                quick_wins[["priority","keyword","category","opportunity"]]
                  .style.apply(style_intent, subset=["category"])
            )
            st.dataframe(quick_wins_styled, use_container_width=True)
        
        # Keyword selection for brief generation
        st.markdown("### 📝 Select a keyword for content brief")
        selected_keyword = st.selectbox(
            "Choose a keyword to generate a content brief:",
            options=[""] + df["keyword"].tolist(),
            index=0,
            placeholder="Select a keyword..."
        )
        
        if selected_keyword:
            st.session_state.selected_keyword = selected_keyword
            st.success(f"✅ Selected: **{selected_keyword}**")
    
    # Navigation buttons
    st.divider()
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("← Back to Inputs"):
            st.session_state.ux_step = 1
            st.rerun()
    with col2:
        disabled = not st.session_state.get("selected_keyword")
        if st.button("Next: Generate Brief →", type="primary", disabled=disabled):
            st.session_state.ux_step = 3
            st.rerun()

def render_step_3():
    st.subheader("Step 3 — AI Content Brief")
    
    keyword = st.session_state.get("selected_keyword")
    if not keyword:
        st.error("No keyword selected. Please go back to Step 2.")
        return
    
    st.info(f"📝 **Generating brief for:** {keyword}")
    
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
        st.markdown("### 📋 Generated Content Brief")
        
        if is_json:
            md = brief_to_markdown(data)
            st.markdown(md)
            
            # Download button
            st.download_button(
                "⬇️ Download Brief (Markdown)",
                data=md.encode("utf-8"),
                file_name=f"{keyword.replace(' ', '-')}__{st.session_state.variant}.md",
                mime="text/markdown",
                use_container_width=True,
            )
            
            # Debug info
            with st.expander("🔧 Debug Info"):
                st.json(data)
                if "brief_prompt" in st.session_state:
                    st.markdown("**Prompt Used:**")
                    st.code(st.session_state.brief_prompt, language="markdown")
                if "brief_latency" in st.session_state:
                    st.caption(f"⏱️ Generated in {st.session_state.brief_latency:.0f}ms")
        else:
            st.warning("⚠️ Model returned non-JSON output. Showing raw:")
            st.markdown(output or "_No output_")
        
        # Feedback section
        st.markdown("---")
        st.markdown("### 💭 How was this brief?")
        rating = st.slider("Rating (1=poor, 5=excellent)", min_value=1, max_value=5, value=4)
        notes = st.text_area("Optional feedback (what was good/bad?)", placeholder="e.g., missing competitor analysis, great structure...")
        
        if st.button("💾 Save Feedback"):
            log_eval(
                variant=st.session_state.variant,
                keyword=keyword,
                prompt=st.session_state.get("brief_prompt", ""),
                output=output,
                latency_ms=st.session_state.get("brief_latency", 0),
                tokens_prompt=st.session_state.get("brief_usage", {}).get("prompt_tokens") if st.session_state.get("brief_usage") else None,
                tokens_completion=st.session_state.get("brief_usage", {}).get("completion_tokens") if st.session_state.get("brief_usage") else None,
                user_rating=rating,
                user_notes=notes,
                extra={
                    "app_version": "wizard-v1",
                    "is_json": is_json,
                    "output_chars": len(output or '')
                },
            )
            st.success("✅ Feedback saved! This helps improve the AI prompts.")
    
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

