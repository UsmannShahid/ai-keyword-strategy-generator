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

# OpenAI SDK (current usage style)
# pip install --upgrade openai
from openai import OpenAI

# ------------- App / Model Config ----------------
MODEL_NAME = "gpt-4o-mini"     # cost-effective, good for structure
MAX_TOKENS = 700               # generous headroom for 12+ keywords in JSON

# ------------- One-time Setup --------------------
load_dotenv()  # Load environment variables from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Fail fast if key is missing, with a clear message
if not OPENAI_API_KEY:
    st.error("Missing OPENAI_API_KEY. Add it to your .env file.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="AI Keyword Tool", page_icon="🔍", layout="centered")
st.title("🔍 AI Keyword Strategy Generator")

# Keep a simple in-memory history for this session
if "history" not in st.session_state:
    st.session_state.history = []

# ------------- Small Utilities -------------------
def slugify(text: str) -> str:
    """Create a simple filename-friendly slug from a string."""
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in text.strip())[:60].strip("-")

def build_prompt(business_desc: str, industry: str, audience: str, location: str) -> str:
    """Return a strict-JSON prompt instructing the model to group keywords by intent."""
    return f"""
You are an expert SEO specialist. For this business, generate 12 keyword ideas grouped by intent.

BUSINESS:
- Description: {business_desc}
- Industry: {industry}
- Target audience: {audience}
- Location/Market: {location}

OUTPUT REQUIREMENTS:
Return ONLY valid JSON (no backticks, no commentary) in this exact shape:
{{
  "informational": ["...","..."],
  "transactional": ["...","..."],
  "branded": ["..."]  // can be empty if none
}}
""".strip()

def get_keywords_json(prompt: str) -> dict:
    """
    Call OpenAI with guardrails to prefer strict JSON.
    Returns a Python dict (parsed JSON) or raises an Exception.
    """
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.5,  # lower temp => more consistent structure
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": "You only return valid JSON. No prose, no code fences."},
            {"role": "user", "content": prompt},
        ],
    )

    # Extract raw text from the first choice
    raw = resp.choices[0].message.content

    # Parse JSON (will raise JSONDecodeError if invalid)
    return json.loads(raw)

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
            prompt = build_prompt(business_desc, industry, audience, location)
            data = get_keywords_json(prompt)  # dict (informational/transactional/branded)

            # Build table
            df = to_dataframe(data)

            if df.empty:
                st.info("No keywords returned. Try broadening your description or removing constraints.")
            else:
                st.success(f"Generated {len(df)} keywords.")
                st.markdown("### 🗂️ Categorized Keywords")
                st.dataframe(df, use_container_width=True)

                # Download as CSV (nice filename with date + slug)
                today = datetime.now().strftime("%Y-%m-%d")
                base = slugify(business_desc) or "keywords"
                csv_name = f"{base}-{today}.csv"
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", data=csv_bytes, file_name=csv_name, mime="text/csv")

                # Quick markdown by category (also nice for copy-paste)
                st.markdown("### Quick View (by category)")
                for cat in ("informational", "transactional", "branded"):
                    kws = data.get(cat) or []
                    if kws:
                        st.markdown(f"**{cat.title()}**")
                        st.markdown("- " + "\n- ".join(kws))

                # Save lightweight run history (for the sidebar)
                st.session_state.history.append({
                    "business": business_desc,
                    "industry": industry,
                    "audience": audience,
                    "location": location,
                    "count": len(df),
                    "ts": today,
                })

        except json.JSONDecodeError:
            # If the model slips and returns non-JSON text
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
