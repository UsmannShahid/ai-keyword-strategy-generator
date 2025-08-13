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

# OpenAI SDK (current usage style)
# pip install --upgrade openai
from openai import OpenAI

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

# ------------- UI: Inputs ------------------------
business_desc = st.text_input("Describe your website or business:")

# Prompt strategy toggle
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

col1, col2, col3 = st.columns(3)
with col1:
    industry = st.text_input("Industry (e.g., skincare, SaaS, fitness)", "")
with col2:
    audience = st.text_input("Target audience (e.g., beginners, SMBs)", "")
with col3:
    location = st.text_input("Location/Market (e.g., US, UK, Toronto)", "")

# ------------- Action: Generate ------------------
if st.button("Generate Keywords"):
    # Basic validation (prevents empty requests)
    if not business_desc.strip():
        st.warning("Please describe your business to generate keywords.")
        st.stop()

    with st.spinner("Generating keywords..."):
        try:
            # Use the new service to generate keywords with selected prompt
            data = st.session_state.keyword_service.generate_keywords(
                business_desc=business_desc,
                industry=industry,
                audience=audience,
                location=location,
                prompt_template=selected_prompt
            )

            # 2) Build table from parsed data
            df = to_dataframe(data)
            
            # Add scoring and priority
            df = add_scores(df, intent_col="category", kw_col="keyword")

            if df.empty:
                st.info("No keywords returned. Try broadening your description or removing constraints.")
            else:
                st.success(f"Generated {len(df)} keywords.")
                st.markdown("""
### 🗂️ Categorized Keywords
**Opportunity** <span title="A 0–100 estimate of keyword potential based on intent, specificity, commercial terms, and estimated competition.">ℹ️</span>
""", unsafe_allow_html=True)
                df = df.sort_values(["priority"]).reset_index(drop=True)
                styled = (
                    df[["priority","keyword","category","opportunity"]]
                      .style.apply(style_intent, subset=["category"])
                )
                st.dataframe(styled, use_container_width=True)

                # Quick wins section
                top_n = 15
                quick_wins = df.sort_values(["opportunity","keyword"], ascending=[False, True]).head(top_n)

                with st.expander(f"⚡ Quick Wins (Top {top_n} by Opportunity)", expanded=True):
                    st.caption(f"{len(quick_wins)} suggestions shown")
                    quick_wins_styled = (
                        quick_wins[["priority","keyword","category","opportunity"]]
                          .style.apply(style_intent, subset=["category"])
                    )
                    st.dataframe(quick_wins_styled, use_container_width=True)
                    # Optional: title ideas via simple template (LLM-based later)
                    st.markdown("#### Suggested Titles")
                    for _, row in quick_wins.iterrows():
                        if row["category"] == "transactional":
                            idea = f"Best {row['keyword'].title()} in {location or '2025'}: Pricing, Pros & Cons"
                        else:
                            idea = f"How to Choose {row['keyword'].title()} ({location or '2025'} Guide)"
                        st.markdown(f"- {idea}")
                    
                    # Quick Wins copy functionality
                    copy_pairs = st.toggle("Copy Quick Wins as CSV (keyword,category)", value=False)
                    render_copy_from_dataframe(
                        df.sort_values("priority").head(15),
                        include_category=copy_pairs,
                        delimiter="\n",
                        label="Copy Quick Wins"
                    )

                # 3) Copy options with toggle for format
                copy_pairs = st.toggle("Copy as CSV (keyword,category)", value=False)
                render_copy_from_dataframe(
                    df,
                    column="keyword",
                    delimiter="\n",
                    label="Copy keyword list" if not copy_pairs else "Copy as CSV pairs",
                    include_category=copy_pairs
                )

                # Brief generation placeholder
                selected = st.multiselect(
                    "Select keywords to generate briefs",
                    options=df["keyword"].tolist(),
                    max_selections=10
                )
                st.button("Generate Briefs (coming soon)", disabled=not selected)

                # 4) Report name input -> nice CSV filename (slugified)
                report_name = st.text_input(
                    "Report name",
                    value=default_report_name(business_desc),
                    help="Used to name the CSV file you download."
                )
                if not report_name.strip():
                    st.warning("Report name is empty. A generic name will be used.")
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv_bytes,
                    file_name=f"{slugify(report_name)}.csv",
                    mime="text/csv",
                )

                # 5) Quick markdown by category (nice for copy-paste)
                st.markdown("### Quick View (by category)")
                for cat in ("informational", "transactional", "branded"):
                    kws = (data.get(cat) or []) if isinstance(data, dict) else []
                    if kws:
                        st.markdown(f"**{cat.title()}**")
                        st.markdown("- " + "\n- ".join(map(str, kws)))

                # 6) Save lightweight run history (for the sidebar)
                today = datetime.now().strftime("%Y-%m-%d")
                st.session_state.history.append({
                    "business": business_desc,
                    "industry": industry,
                    "audience": audience,
                    "location": location,
                    "count": len(df),
                    "ts": today,
                })

        except json.JSONDecodeError:
            # Kept for backward-compat if you still call a JSON-returning helper elsewhere.
            st.error("The model returned invalid JSON. Please try again or simplify inputs.")
        except Exception as e:
            # Network issues / API errors / key problems
            st.error(f"Error generating keywords: {e}")
            st.info("Check your OpenAI API key, internet connection, or try again in a minute.")

# ------------- Content Brief Generator with A/B Testing -----------
st.markdown("---")
st.markdown("## 📝 AI Content Brief Generator")

# --- Persisted variant selection ---
if "variant" not in st.session_state:
    # Default to first available
    st.session_state.variant = (prompt_manager.get_variants("content_brief") or ["A"])[0]

variants = prompt_manager.get_variants("content_brief")
st.session_state.variant = st.selectbox(
    "Prompt Variant (A/B)",
    variants if variants else ["A"],
    index=(variants.index(st.session_state.variant) if variants and st.session_state.variant in variants else 0)
)

# --- Inputs ---
keyword = st.text_input("Enter keyword", placeholder="e.g., best ergonomic chair for home office")

# --- Action ---
if st.button("Generate Brief", type="primary") and keyword:
    with st.spinner("Generating brief..."):
        output, prompt_used, latency_ms, usage = generate_brief_with_variant(
            keyword=keyword,
            variant=st.session_state.variant,
        )

    st.subheader("AI Content Brief")
    
    # Parse output and detect issues
    data, is_json = parse_brief_output(output)
    
    auto_flags = []
    # Heuristic 1: placeholder detection
    if is_json and detect_placeholders(data):
        auto_flags.append("Detected generic placeholders (e.g., 'Chair Name #1').")
    # Heuristic 2: very short output
    if (output or '').strip() and len(output.strip()) < 400:
        auto_flags.append("Output is quite short (<400 chars) – may be truncated or low quality.")
    # Heuristic 3: missing headings if JSON has structure but few sections
    if is_json and isinstance(data, dict):
        # Count plausible section keys
        section_keys = [k for k in data.keys() if any(token in k.lower() for token in ["intro","outline","h1","h2","sections","faq","conclusion","title"])]
        if len(section_keys) <= 2:
            auto_flags.append("Parsed JSON has very few structured sections – might be incomplete.")
    # Heuristic 4: count of markdown headings in raw output (only for non-JSON outputs)
    if output and not is_json and output.count("\n#") < 2 and output.lower().count("##") < 2:
        auto_flags.append("Few or no markdown headings detected – consider prompting for structured outline.")

    # Show auto-detected flags if any
    if auto_flags:
        st.warning("⚠️ **Auto-detected issues:**")
        for flag in auto_flags:
            st.markdown(f"- {flag}")
    
    st.markdown(output or "_No output_")
    
    # Optional: show parsed JSON if available
    if is_json and isinstance(data, dict):
        with st.expander("Parsed JSON Structure"):
            st.json(data)

    with st.expander("Debug / Prompt Details"):
        st.code(prompt_used, language="markdown")
        if usage:
            st.json(usage)
        st.caption(f"Latency: {latency_ms:.0f} ms")

    # --- Feedback & Logging ---
    st.markdown("---")
    st.subheader("How good was this brief?")
    rating = st.slider("Rating (1=poor, 5=excellent)", min_value=1, max_value=5, value=4)
    notes = st.text_area("Optional notes (what was good/bad, missing headings, etc.)")

    if st.button("Save outcome"):
        tokens_prompt = usage.get("prompt_tokens") if usage else None
        tokens_completion = usage.get("completion_tokens") if usage else None
        log_eval(
            variant=st.session_state.variant,
            keyword=keyword,
            prompt=prompt_used,
            output=output,
            latency_ms=latency_ms,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            user_rating=rating,
            user_notes=notes,
            extra={
                "app_version": "beta-mvp",
                "auto_flags": auto_flags,
                "is_json": is_json,
                "output_chars": len(output or '')
            },
        )
        st.success("Saved! This run is now logged for A/B analysis.")

# ------------- Sidebar: Help + History -----------
st.sidebar.title("How to Use")
st.sidebar.markdown("""
1. Describe your business (be specific).
2. Optionally add industry, audience, and location.
3. Click **Generate Keywords**.
4. Review, copy, or download as CSV.

**Tip:** The more specific the description, the better the keywords.
""")

st.sidebar.title("Recent Runs (session)")
if st.session_state.history:
    for item in st.session_state.history[-5:][::-1]:
        st.sidebar.write(
            f"- **{item['business'][:30]}** · {item['count']} kws · {item['ts']}"
        )

st.sidebar.title("About")
st.sidebar.markdown("""
This tool uses OpenAI to generate SEO-friendly keyword ideas grouped by intent,
based on your business context. Built with Streamlit + Python.
""")
