import streamlit as st
import pandas as pd
from eval_utils import load_evals_df

st.set_page_config(page_title="Compare Runs", page_icon="📊", layout="wide")
st.title("📊 Compare Runs (A/B)")

# Navigation links
try:
    st.sidebar.page_link("app.py", label="🏠 Main App")
except Exception:
    pass

df = load_evals_df()

if df.empty:
    st.info("No evaluation data yet. Generate a few briefs and click **Save outcome** to populate logs.")
    st.stop()

# --- Filters ---
with st.sidebar:
    st.header("Filters")
    keywords = sorted([k for k in df["keyword"].dropna().unique() if k])
    kw = st.selectbox("Keyword", options=["(all)"] + keywords, index=0)
    variants = sorted([v for v in df["variant"].dropna().unique() if v])
    selected_variants = st.multiselect("Variants", options=variants, default=variants)
    max_rows = st.slider("Rows to show", 10, 200, 50)

fdf = df.copy()
if kw != "(all)":
    fdf = fdf[fdf["keyword"] == kw]
if selected_variants:
    fdf = fdf[fdf["variant"].isin(selected_variants)]

if fdf.empty:
    st.warning("No rows match your filters.")
    st.stop()

# --- Aggregates by variant ---
agg = fdf.groupby("variant").agg(
    runs=("id","count"),
    avg_rating=("user_rating","mean"),
    avg_latency_ms=("latency_ms","mean"),
    avg_output_chars=("output_chars","mean"),
    avg_prompt_tokens=("tokens_prompt","mean"),
    avg_completion_tokens=("tokens_completion","mean"),
).reset_index()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Runs", int(fdf["id"].count()))
with col2:
    st.metric("Avg Rating (all)", round(fdf["user_rating"].mean(), 2))
with col3:
    st.metric("Avg Latency (ms, all)", int(fdf["latency_ms"].mean()))

st.subheader("Variant Summary")
st.dataframe(
    agg.style.format({
        "avg_rating":"{:.2f}",
        "avg_latency_ms":"{:.0f}",
        "avg_output_chars":"{:.0f}",
        "avg_prompt_tokens":"{:.0f}",
        "avg_completion_tokens":"{:.0f}",
    }),
    use_container_width=True,
)

# --- Recent runs table ---
st.subheader("Recent Runs")
cols = ["ts","keyword","variant","user_rating","latency_ms","output_chars","auto_flags"]
show = fdf[cols].head(max_rows)
st.dataframe(show, use_container_width=True)

# --- Download CSV ---
csv = fdf.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv, file_name="ab_evals_filtered.csv", mime="text/csv")
