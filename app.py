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
from services import KeywordService
from parsing import SAFE_OUTPUT

# OpenAI SDK (current usage style)
# pip install --upgrade openai
from openai import OpenAI

# ------------- One-time Setup --------------------
load_dotenv()  # Load environment variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
            # Use the new service to generate keywords
            data = st.session_state.keyword_service.generate_keywords(
                business_desc=business_desc,
                industry=industry,
                audience=audience,
                location=location
            )

            # 2) Build table from parsed data
            df = to_dataframe(data)

            if df.empty:
                st.info("No keywords returned. Try broadening your description or removing constraints.")
            else:
                st.success(f"Generated {len(df)} keywords.")
                st.markdown("### 🗂️ Categorized Keywords")
                st.dataframe(df, use_container_width=True)

                # 3) Copy options with toggle for format
                copy_pairs = st.toggle("Copy as CSV (keyword,category)", value=False)
                render_copy_from_dataframe(
                    df,
                    column="keyword",
                    delimiter="\n",
                    label="Copy keyword list" if not copy_pairs else "Copy as CSV pairs",
                    include_category=copy_pairs
                )

                # 4) Report name input -> nice CSV filename (slugified)
                report_name = st.text_input(
                    "Report name",
                    value=default_report_name(business_desc),
                    help="Used to name the CSV file you download."
                )
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
