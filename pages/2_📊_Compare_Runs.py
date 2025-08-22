# pages/2_📊_Compare_Runs.py
from __future__ import annotations
import os, json
from typing import List, Dict, Any
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Compare Runs", page_icon="📊", layout="wide")

LOG_PATH = os.path.join("data", "evals.jsonl")

# ---- Internal-only guard (use new st.query_params) ----
def _get_dev_flag() -> bool:
    # Preferred: new API
    try:
        val = st.query_params.get("dev", "0")
        # st.query_params returns a single string value
        return str(val).lower() in ("1", "true", "yes")
    except Exception:
        # Fallback for older Streamlit
        try:
            qp = st.experimental_get_query_params()
            val = (qp.get("dev") or ["0"])[0]
            return str(val).lower() in ("1", "true", "yes")
        except Exception:
            return False

if _get_dev_flag():
    st.session_state["dev_mode"] = True

if not st.session_state.get("dev_mode", False):
    st.caption("🔒 Internal A/B analysis dashboard (briefs + writer notes). Add `?dev=1` to the URL to enable.")
    st.stop()


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
    st.title("📊 Compare Runs (Internal)")
    st.caption("Internal A/B analysis dashboard for content briefs and writer’s notes.")

    df = load_jsonl(LOG_PATH)
    if df.empty:
        st.info("No logs yet. Generate a brief or writer's notes, then save feedback.")
        return

    # --- Toggle Filter (top) ---
    view_mode = st.radio(
        "Show runs for:",
        ["All Runs", "Content Briefs Only", "Writer's Notes Only"],
        index=0,
        horizontal=True,
    )

    # Apply toggle filter FIRST
    if view_mode == "Content Briefs Only":
        df = df[df["type"] == "content_brief"] if "type" in df.columns else df
    elif view_mode == "Writer's Notes Only":
        df = df[df["type"] == "writer_notes"] if "type" in df.columns else df

    # --- Filters ---
    with st.expander("🔍 Filters", expanded=True):
        c1, c2, c3, c4 = st.columns([1,1,1,1])

        types = sorted([t for t in df["type"].dropna().unique().tolist() if t]) if "type" in df.columns else []
        f_type = c1.multiselect("Type", options=types, default=types or [], help="content_brief / writer_notes")

        variants = sorted([v for v in df["variant"].dropna().unique().tolist() if v]) if "variant" in df.columns else []
        f_variant = c2.multiselect("Variant", options=variants, default=variants or [], help="Prompt variant (A/B for notes; prompt key for briefs)")

        styles = sorted([s for s in df["notes_style"].dropna().unique().tolist() if s]) if "notes_style" in df.columns else []
        f_style = c3.multiselect("Notes Style", options=styles, default=styles or [], help="Concise / Detailed (when available)")

        kw_query = c4.text_input("Keyword contains", value="", placeholder="e.g., ergonomic chair")

        # Date range (optional if ts present)
        if "ts" in df.columns and not df["ts"].dropna().empty:
            d1, d2 = st.columns([1,1])
            min_ts = pd.to_datetime(df["ts"].min())
            max_ts = pd.to_datetime(df["ts"].max())
            start = d1.date_input("From", value=min_ts.date())
            end = d2.date_input("To", value=max_ts.date())

    # Apply filters
    filt = pd.Series([True] * len(df), index=df.index)
    if f_type and "type" in df.columns:
        filt &= df["type"].isin(f_type)
    if f_variant and "variant" in df.columns:
        filt &= df["variant"].isin(f_variant)
    if f_style and "notes_style" in df.columns:
        filt &= df["notes_style"].isin(f_style)
    if kw_query.strip() and "keyword" in df.columns:
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

    if fdf.empty:
        st.info("No data matches your filters.")
        return

    # Ensure has_rating column exists
    if "user_rating" in fdf.columns and "has_rating" not in fdf.columns:
        fdf["has_rating"] = fdf["user_rating"].notna()
    elif "has_rating" not in fdf.columns:
        fdf["has_rating"] = False

    # --- Topline metrics ---
    m1, m2, m3, m4 = st.columns(4)

    # Safe calculation for average chars
    if 'output_chars' in fdf.columns and not fdf.empty:
        chars_series = pd.to_numeric(fdf['output_chars'], errors='coerce').dropna()
        avg_chars = chars_series.mean() if not chars_series.empty else 0
        avg_chars_display = int(avg_chars) if not pd.isna(avg_chars) and avg_chars > 0 else 0
    else:
        avg_chars_display = 0
    m1.metric("Avg Output Length", f"{avg_chars_display} chars")

    # Safe calculation for rating count
    if 'has_rating' in fdf.columns and not fdf.empty:
        rating_sum = fdf['has_rating'].sum()
        runs_with_rating = int(rating_sum) if not pd.isna(rating_sum) else 0
    else:
        runs_with_rating = 0
    m2.metric("Runs with Rating", f"{runs_with_rating}")

    # Safe calculation for type counts
    if 'type' in fdf.columns and not fdf.empty:
        type_counts = fdf['type'].value_counts()
        writer_notes_count = int(type_counts.get('writer_notes', 0))
        briefs_count = int(type_counts.get('content_brief', 0))
    else:
        writer_notes_count = 0
        briefs_count = 0
    m3.metric("Writer's Notes (runs)", f"{writer_notes_count}")
    m4.metric("Briefs (runs)", f"{briefs_count}")

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
    perf_cols = [c for c in ["type","variant","user_rating","output_chars","has_rating"] if c in fdf.columns]
    if len(perf_cols) >= 2 and {"type","variant"}.issubset(fdf.columns) and not fdf.empty:
        # Create performance dataframe with safe numeric conversions
        perf_df = fdf[perf_cols].copy()
        perf_df["output_chars"] = pd.to_numeric(perf_df.get("output_chars", pd.Series(dtype=float)), errors="coerce")
        perf_df["user_rating"] = pd.to_numeric(perf_df.get("user_rating", pd.Series(dtype=float)), errors="coerce")
        perf_df["has_rating"] = perf_df.get("has_rating", False)
        
        # Group and aggregate with safety checks
        grouped = perf_df.groupby(["type","variant"], dropna=False, observed=False)
        
        # Perform aggregations with fallback for empty groups
        try:
            perf = grouped.agg(
                runs=("variant","count"),
                avg_chars=("output_chars","mean"),
                rated=("has_rating","sum"),
                avg_rating=("user_rating","mean"),
            ).reset_index()
        except Exception:
            # Fallback if aggregation fails
            perf = pd.DataFrame(columns=["type", "variant", "runs", "avg_chars", "rated", "avg_rating"])

        if not perf.empty:
            # Clean up the results with safe conversions
            if "avg_chars" in perf.columns:
                perf["avg_chars"] = perf["avg_chars"].fillna(0).apply(lambda x: int(x) if not pd.isna(x) else 0)
            if "avg_rating" in perf.columns:
                perf["avg_rating"] = perf["avg_rating"].fillna(0).round(2)
            if "runs" in perf.columns and "rated" in perf.columns:
                # Safe percentage calculation
                perf["% rated"] = perf.apply(
                    lambda row: round((row["rated"] / row["runs"]) * 100, 1) 
                    if row["runs"] > 0 else 0, axis=1
                )

        st.subheader("📊 Variant comparison (chart)")
        metric_choice = st.selectbox(
            "Metric",
            ["Average rating", "Average output length (chars)"],
            index=0,
            help="Switch the metric to compare variants."
        )

        if not perf.empty:
            chart_df = perf.copy()
            ycol = "avg_rating" if metric_choice == "Average rating" else "avg_chars"
            st.caption(
                "Bars show average user rating per type/variant (filtered)." if ycol == "avg_rating"
                else "Bars show average output length per type/variant (filtered)."
            )
            chart_df[ycol] = chart_df[ycol].fillna(0)

            # Pivot so each 'type' becomes a series; index = variant
            try:
                pivot = chart_df.pivot(index="variant", columns="type", values=ycol)
                if not pivot.empty:
                    pivot = pivot.fillna(0)
                    # Show runs context in a caption (optional)
                    runs_info = (
                        chart_df.groupby(["type","variant"])["runs"].sum()
                        .unstack(0).fillna(0).astype(int)
                    )
                    st.caption(f"Runs (by variant/type): {runs_info.to_dict()}")
                    st.bar_chart(pivot, use_container_width=True)
                else:
                    st.info("No data available for comparison chart.")
            except Exception as e:
                st.info(f"Cannot render chart: not enough data for pivot table.")
        else:
            st.info("Charts will appear after you have runs with type and variant.")

        # Histogram -- Output length distribution
        st.subheader("🧮 Output length distribution")
        if "output_chars" in fdf.columns and not fdf.empty:
            hist_df = fdf.copy()
            hist_df["output_chars"] = pd.to_numeric(hist_df["output_chars"], errors="coerce")
            # Remove NaN values and ensure non-negative
            hist_df = hist_df.dropna(subset=["output_chars"])
            if not hist_df.empty:
                hist_df["output_chars"] = hist_df["output_chars"].clip(lower=0)
                if hist_df["output_chars"].sum() > 0:
                    bins = [0, 500, 1000, 1500, 2000, 3000, 5000, 8000, 12000]
                    labels = [f"{bins[i]}–{bins[i+1]-1}" for i in range(len(bins)-1)]
                    hist_df["len_bucket"] = pd.cut(hist_df["output_chars"], bins=bins, labels=labels, include_lowest=True)
                    bucket_counts = hist_df.groupby("len_bucket", observed=False).size().reset_index(name="runs")
                    bucket_counts = bucket_counts.sort_values(by="len_bucket", ascending=True)
                    if not bucket_counts.empty and bucket_counts["runs"].sum() > 0:
                        st.bar_chart(bucket_counts, x="len_bucket", y="runs", use_container_width=True)
                    else:
                        st.info("No valid output length data to chart.")
                else:
                    st.info("No output length data to chart.")
            else:
                st.info("No valid output length data to chart.")
        else:
            st.info("No output length data to chart.")

        st.subheader("📈 Variant performance (by type & variant)")
        if not perf.empty:
            display_cols = [c for c in ["type","variant","runs","avg_chars","% rated","avg_rating"] if c in perf.columns]
            st.dataframe(perf[display_cols], use_container_width=True)
        else:
            st.info("No performance data available.")
    else:
        st.info("Variant performance will appear after you have runs with type and variant.")

    # --- Compact table view ---
    show_cols = [c for c in ["ts","type","variant","notes_style","keyword","user_rating","output_chars","qw_explain"] if c in fdf.columns]
    if not fdf.empty and show_cols:
        st.dataframe(
            fdf[show_cols],
            use_container_width=True,
            height=min(600, 48 + 33*min(len(fdf), 12))
        )
    else:
        st.info("No data to display in table.")

    st.divider()

    # --- Row inspector ---
    st.subheader("🔎 Inspect a run")
    if fdf.empty:
        st.info("No rows match filters.")
        return

    def _label(r):
        try:
            ts = str(r.get("ts",""))[:19].replace("T"," ") if r.get("ts") else ""
            typ = str(r.get("type","")) if r.get("type") else "-"
            var = str(r.get("variant","")) if r.get("variant") else "-"
            kw = str(r.get("keyword","")) if r.get("keyword") else "-"
            return f"{ts} • {typ} • v{var} • {kw}"
        except Exception:
            return f"Row {fdf.index.tolist().index(r.name) if hasattr(r, 'name') else '?'}"

    try:
        options = fdf.to_dict(orient="records")
        if not options:
            st.info("No data available for inspection.")
            return
            
        label_map = {_label(r): r for r in options}
        sel_label = st.selectbox("Pick a run to inspect", options=list(label_map.keys()), index=0)
        row = label_map[sel_label]
    except Exception as e:
        st.error(f"Error preparing row data: {str(e)}")
        return

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
