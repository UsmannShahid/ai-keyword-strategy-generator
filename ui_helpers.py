# ai_keyword_tool/ui_helpers.py

from __future__ import annotations
import json
from typing import Iterable, Optional
import streamlit as st
import streamlit.components.v1 as components


def render_copy_to_clipboard(text: str, label: str = "Copy to clipboard") -> None:
    """
    Render a small HTML/JS button that copies `text` to the user's clipboard.
    - Uses JSON encoding to safely handle quotes, newlines, special characters.
    - Shows a small "Copied!" toast in the bottom-right corner when clicked.
    """
    # Encode the text as a JSON string so JavaScript can safely read it
    payload = json.dumps(text or "")

    # Render raw HTML/JavaScript into the Streamlit app
    components.html(
        f"""
        <button
          style="
            padding:8px 12px;
            border:none;
            border-radius:8px;
            background:#2563eb;
            color:#fff;
            cursor:pointer
          "
          onclick='
            navigator.clipboard.writeText({payload}).then(() => {{
              // Create a toast notification element
              const t = document.createElement("div");
              t.innerText = "Copied!";
              t.style.position = "fixed";
              t.style.bottom = "16px";
              t.style.right = "16px";
              t.style.padding = "8px 12px";
              t.style.background = "#16a34a";
              t.style.color = "#fff";
              t.style.borderRadius = "8px";
              t.style.boxShadow = "0 2px 8px rgba(0,0,0,0.15)";

              // Add toast to the page
              document.body.appendChild(t);

              // Remove toast after 1.2 seconds
              setTimeout(() => t.remove(), 1200);
            }})
          '
        >{label}</button>
        """,
        height=40,  # Reserve a bit of space in the layout
    )

def render_copy_from_dataframe(
    df,
    column: str = "keyword",
    delimiter: str = "\n",
    label: Optional[str] = None,
    transform: Optional[callable] = None,
    include_category: bool = False,
    category_column: str = "category",
    max_chars: int = 200_000,
) -> None:
    """
    Render a copy button that copies values from a DataFrame.

    - Trims whitespace, drops NaNs/blanks.
    - Optionally copies "keyword,category" pairs.
    - Warns if content is very large (clipboard limits vary by OS/browser).
    """
    if df is None or df.empty:
        st.info("Nothing to copy yet.")
        return
    if column not in df.columns:
        st.info(f"Nothing to copy. Column `{column}` not found.")
        return

    series = df[column].astype(str).str.strip()
    series = series[series.astype(bool)]  # drop empty strings

    if transform:
        series = series.map(transform)

    if include_category and category_column in df.columns:
        # Build "keyword,category" lines
        cat = df.loc[series.index, category_column].astype(str).str.strip()
        items = [f"{k},{c}" for k, c in zip(series.tolist(), cat.tolist())]
    else:
        items = series.tolist()

    if not items:
        st.info("Nothing to copy after filtering.")
        return

    text = delimiter.join(items)

    # Gentle guardrail for extremely large payloads
    if len(text) > max_chars:
        st.warning(
            f"Copy content is quite large ({len(text):,} chars). "
            "Some browsers may truncate the clipboard."
        )

    btn_label = label or f"Copy {column} list ({len(items)})"
    render_copy_to_clipboard(text, btn_label)
