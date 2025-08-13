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

st.caption("Quick side-by-side metrics for recent prompt variant runs.")

df = load_evals_df()
if df.empty:
    st.info("No evaluation logs yet. Generate briefs and save outcomes to see comparisons here.")
    st.stop()

# Basic filters
colf1, colf2, colf3 = st.columns(3)
with colf1:
    variant_filter = st.multiselect("Variants", sorted(df.variant.dropna().unique().tolist()), default=sorted(df.variant.dropna().unique().tolist()))
with colf2:
    keyword_search = st.text_input("Keyword contains")
with colf3:
    show_flags_only = st.checkbox("Only flagged (auto_flags)", value=False)

mask = pd.Series([True]*len(df))
if variant_filter:
    mask &= df.variant.isin(variant_filter)
if keyword_search:
    mask &= df.keyword.fillna("").str.contains(keyword_search, case=False, na=False)
if show_flags_only:
    mask &= df.auto_flags.apply(lambda x: bool(x))

filtered = df[mask].copy()

if filtered.empty:
    st.warning("No rows match your filters.")
    st.stop()

# Aggregate summary
summary = filtered.groupby('variant').agg(
    runs=('id','count'),
    avg_rating=('user_rating','mean'),
    p50_latency=('latency_ms', lambda s: s.dropna().median()),
    avg_latency=('latency_ms','mean'),
    avg_chars=('output_chars','mean'),
    flagged_pct=('auto_flags', lambda s: (s.apply(lambda x: bool(x)).mean()*100.0) if len(s)>0 else 0)
).reset_index()

st.subheader("Variant Summary")
st.dataframe(summary.style.format({
    'avg_rating': '{:.2f}',
    'p50_latency': '{:.0f}',
    'avg_latency': '{:.0f}',
    'avg_chars': '{:.0f}',
    'flagged_pct': '{:.1f}%'
}), use_container_width=True)

# Recent runs table
st.subheader("Recent Runs")
show_cols = ['ts','variant','keyword','user_rating','latency_ms','output_chars','auto_flags']
missing_cols = [c for c in show_cols if c not in filtered.columns]
for c in missing_cols:
    filtered[c] = None
st.dataframe(filtered[show_cols].head(200), use_container_width=True)

# Drill-down
st.subheader("Drill-down")
selected_keyword = st.selectbox("Pick a keyword to compare outputs", ['(select)'] + sorted(filtered.keyword.dropna().unique().tolist()))
if selected_keyword and selected_keyword != '(select)':
    subset = filtered[filtered.keyword == selected_keyword].sort_values('ts', ascending=False)
    for _, row in subset.iterrows():
        with st.expander(f"{row['ts']} · Variant {row['variant']} · Rating {row.get('user_rating','?')}"):
            st.markdown(f"**Latency:** {row.get('latency_ms','?')} ms | **Chars:** {row.get('output_chars','?')}")
            if row.get('auto_flags'):
                st.warning("Flags: " + "; ".join(row['auto_flags']))
            # Show truncated prompt & output if present
            prompt = row.get('prompt')
            if prompt:
                st.markdown("**Prompt (first 600 chars)**")
                st.code(prompt[:600] + ('…' if len(prompt)>600 else ''))
            output = row.get('output') or ''
            st.markdown("**Output (first 1200 chars)**")
            st.text(output[:1200] + ('…' if len(output)>1200 else ''))
