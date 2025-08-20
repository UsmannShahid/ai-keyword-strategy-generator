# pages/2_📊_Compare_Runs.py
from __future__ import annotations
import os, json
from typing import List, Dict, Any
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Compare Runs", page_icon="📊", layout="wide")

LOG_PATH = os.path.join("data", "evals.jsonl")

@st.cache_data(show_spinner=False)
def load_jsonl(path: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return pd.DataFrame()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # skip malformed lines but keep going
                continue
    if not rows:
        return pd.DataFrame()
    df = pd.json_normalize(rows)
    # Normalize common fields
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    if "output_chars" in df.columns:
        df["output_chars"] = pd.to_numeric(df["output_chars"], errors="coerce")
    # convenience columns
    if "extra.type" in df.columns:
        df.rename(columns={"extra.type": "type"}, inplace=True)
    elif "type" not in df.columns and "extra" in df.columns:
        # try to extract type if extra is dict in some rows
        df["type"] = df["extra"].apply(lambda x: (x or {}).get("type") if isinstance(x, dict) else None)
    # Writer notes style, if present
    if "extra.writer_notes_style_label" in df.columns:
        df.rename(columns={"extra.writer_notes_style_label": "notes_style"}, inplace=True)
    else:
        df["notes_style"] = None
    if "extra.writer_notes_variant" in df.columns:
        df.rename(columns={"extra.writer_notes_variant": "notes_variant"}, inplace=True)
    else:
        df["notes_variant"] = None
    # Quick-win explanation if present
    if "extra.quickwin_explanation" in df.columns:
        df.rename(columns={"extra.quickwin_explanation": "qw_explain"}, inplace=True)
    else:
        df["qw_explain"] = None
    # Rating present?
    if "user_rating" in df.columns:
        df["has_rating"] = df["user_rating"].notna()
    else:
        df["has_rating"] = False
    # Sort newest first
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False)
    return df

def main():
    st.title("📊 Compare Runs")
    st.caption("Browse and filter your brief generations and writer’s notes. Use this to compare A/B variants and quality over time.")

    df = load_jsonl(LOG_PATH)
    if df.empty:
        st.info("No logs yet. Generate a brief or writer’s notes, then save feedback.")
        return

    # --- Filters ---
    with st.expander("🔍 Filters", expanded=True):
        c1, c2, c3, c4 = st.columns([1,1,1,1])

        types = sorted([t for t in df["type"].dropna().unique().tolist() if t])
        f_type = c1.multiselect("Type", options=types, default=types or None, help="content_brief / writer_notes")

        variants = sorted([v for v in df["variant"].dropna().unique().tolist() if v])
        f_variant = c2.multiselect("Variant", options=variants, default=variants or None, help="Prompt variant (A/B for notes; prompt key for briefs)")

        styles = sorted([s for s in df["notes_style"].dropna().unique().tolist() if s])
        f_style = c3.multiselect("Notes Style", options=styles, default=styles or None, help="Concise / Detailed (when available)")

        kw_query = c4.text_input("Keyword contains", value="", placeholder="e.g., ergonomic chair")

        # Date range (optional if ts present)
        if "ts" in df.columns and not df["ts"].dropna().empty:
            d1, d2 = st.columns([1,1])
            min_ts = pd.to_datetime(df["ts"].min())
            max_ts = pd.to_datetime(df["ts"].max())
            start = d1.date_input("From", value=min_ts.date())
            end = d2.date_input("To", value=max_ts.date())

    filt = pd.Series([True] * len(df))
    if f_type:
        filt &= df["type"].isin(f_type)
    if f_variant:
        filt &= df["variant"].isin(f_variant)
    if f_style:
        filt &= df["notes_style"].isin(f_style)
    if kw_query.strip():
        filt &= df["keyword"].fillna("").str.contains(kw_query.strip(), case=False, na=False)
    if "ts" in df.columns and not df["ts"].dropna().empty:
        try:
            start_ts = pd.to_datetime(start)
            end_ts = pd.to_datetime(end) + pd.Timedelta(days=1)  # inclusive
            filt &= df["ts"].between(start_ts, end_ts)
        except Exception:
            pass

    fdf = df.loc[filt].copy()
    st.write(f"Showing **{len(fdf)}** of {len(df)} runs.")

    # ---- Export (filtered) as CSV ----
    csv_bytes = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export filtered runs (CSV)",
        data=csv_bytes,
        file_name="eval_runs_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ---- Variant performance table (by type & variant) ----
    perf_cols = []
    for c in ["type","variant","user_rating","output_chars","has_rating"]:
        if c in fdf.columns:
            perf_cols.append(c)

    if {"type","variant"}.issubset(fdf.columns):
        perf = (
            fdf[perf_cols]
            .assign(
                output_chars=pd.to_numeric(fdf.get("output_chars", pd.Series(dtype=float)), errors="coerce"),
                user_rating=pd.to_numeric(fdf.get("user_rating", pd.Series(dtype=float)), errors="coerce"),
                has_rating=fdf.get("has_rating", False),
            )
            .groupby(["type","variant"], dropna=False)
            .agg(
                runs=("variant","count"),
                avg_chars=("output_chars","mean"),
                rated=("has_rating","sum"),
                avg_rating=("user_rating","mean"),
            )
            .reset_index()
        )

        st.subheader("📊 Variant comparison (chart)")

        # Bar Chart - Avg rating (fallback to length)

        metric_choice = st.selectbox(
            "Metric",
            ["Average rating", "Average output length (chars)"],
            index=0,
            help="Switch the metric to compare variants."
        )

        if {"type","variant"}.issubset(fdf.columns):
            chart_df = (
                fdf.assign(
                    user_rating=pd.to_numeric(fdf.get("user_rating", pd.Series(dtype=float)), errors="coerce"),
                    output_chars=pd.to_numeric(fdf.get("output_chars", pd.Series(dtype=float)), errors="coerce"),
                )
                .groupby(["type","variant"], dropna=False)
                .agg(
                    avg_rating=("user_rating","mean"),
                    avg_chars=("output_chars","mean"),
                    runs=("variant","count"),
                )
                .reset_index()
            )

            if metric_choice == "Average rating":
                ycol = "avg_rating"
                st.caption("Bars show average user rating per type/variant (filtered).")
            else:
                ycol = "avg_chars"
                st.caption("Bars show average output length per type/variant (filtered).")

            # Replace NaN with 0 to avoid rendering issues
            chart_df[ycol] = chart_df[ycol].fillna(0)

            st.bar_chart(
                data=chart_df,
                x="variant",
                y=ycol,
                color="type",
                use_container_width=True,
            )
        else:
            st.info("Charts will appear after you have runs with type and variant.")


        # Histogram -- Output length distribution
        st.subheader("🧮 Output length distribution")

        if "output_chars" in fdf.columns:
            hist_df = fdf.copy()
            hist_df["output_chars"] = pd.to_numeric(hist_df["output_chars"], errors="coerce").fillna(0).clip(lower=0)
            # Bucket into ranges for readability
            bins = [0, 500, 1000, 1500, 2000, 3000, 5000, 8000, 12000]
            labels = [f"{bins[i]}–{bins[i+1]-1}" for i in range(len(bins)-1)]
            hist_df["len_bucket"] = pd.cut(hist_df["output_chars"], bins=bins, labels=labels, include_lowest=True)

            bucket_counts = hist_df.groupby("len_bucket").size().reset_index(name="runs")
            bucket_counts = bucket_counts.sort_values(by="len_bucket", ascending=True)

            st.bar_chart(bucket_counts, x="len_bucket", y="runs", use_container_width=True)
        else:
            st.info("No output length data to chart.")


        # tidy numbers
        if "avg_chars" in perf.columns:
            perf["avg_chars"] = perf["avg_chars"].fillna(0).round(0).astype(int)
        if "avg_rating" in perf.columns:
            perf["avg_rating"] = perf["avg_rating"].round(2)
        if "runs" in perf.columns and "rated" in perf.columns:
            perf["% rated"] = ((perf["rated"] / perf["runs"]).fillna(0) * 100).round(1)

        st.subheader("📈 Variant performance (by type & variant)")
        st.dataframe(perf[["type","variant","runs","avg_chars","% rated","avg_rating"]], use_container_width=True)
    else:
        st.info("Variant performance will appear after you have runs with type and variant.")



    # --- Topline metrics ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg Output Length", f"{int(fdf['output_chars'].dropna().mean()) if 'output_chars' in fdf else 0} chars")
    m2.metric("Runs with Rating", f"{int(fdf['has_rating'].sum())}")
    m3.metric("Writer’s Notes (runs)", f"{int((fdf['type'] == 'writer_notes').sum())}")
    m4.metric("Briefs (runs)", f"{int((fdf['type'] == 'content_brief').sum())}")

    # --- Compact table view ---
    show_cols = []
    for c in ["ts","type","variant","notes_style","keyword","user_rating","output_chars","qw_explain"]:
        if c in fdf.columns:
            show_cols.append(c)
    st.dataframe(
        fdf[show_cols],
        use_container_width=True,
        height=min(600, 48 + 33*min(len(fdf), 12))
    )

    st.divider()

    # --- Row inspector ---
    st.subheader("🔎 Inspect a run")
    # build options label
    def _label(r):
        ts = str(r.get("ts",""))[:19].replace("T"," ")
        typ = r.get("type","")
        var = r.get("variant","")
        kw  = r.get("keyword","")
        return f"{ts} • {typ or '-'} • v{var or '-'} • {kw or '-'}"

    options = fdf.to_dict(orient="records")
    if not options:
        st.info("No rows match filters.")
        return

    label_map = {_label(r): r for r in options}
    sel_label = st.selectbox("Pick a run to inspect", options=list(label_map.keys()), index=0)
    row = label_map[sel_label]

    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown(f"**Keyword:** {row.get('keyword','—')}")
        st.markdown(f"**Type:** {row.get('type','—')}  |  **Variant:** {row.get('variant','—')}  |  **Notes style:** {row.get('notes_style','—')}")
        if "qw_explain" in row and row.get("qw_explain"):
            st.info(row["qw_explain"])
        st.markdown("**Prompt (truncated)**")
        st.code((row.get("prompt") or "")[:1200], language="markdown")
    with c2:
        st.markdown("**Rating**")
        st.write(row.get("user_rating","—"))
        st.markdown("**Chars**")
        st.write(row.get("output_chars","—"))
        st.markdown("**When**")
        st.write(str(row.get("ts",""))[:19].replace("T"," "))

    with st.expander("Raw JSON row"):
        st.json(row)

    # If extra contains parsed structures, surface them
    if "extra" in row and isinstance(row["extra"], dict):
        ex = row["extra"]
        if "serp_summary" in ex and ex["serp_summary"]:
            with st.expander("SERP Summary"):
                st.json(ex["serp_summary"])
        if "notes_stats" in ex and ex["notes_stats"]:
            with st.expander("Notes Stats"):
                st.json(ex["notes_stats"])
        if "quickwin_breakdown" in ex and ex["quickwin_breakdown"]:
            with st.expander("Quick-Win Breakdown"):
                st.json(ex["quickwin_breakdown"])

if __name__ == "__main__":
    main()
