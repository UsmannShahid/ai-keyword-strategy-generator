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
) -> None:
    """
    Render a copy button that copies all values from a specific DataFrame column.
    
    Args:
        df: The pandas DataFrame to extract from.
        column: The column name to copy (default: "keyword").
        delimiter: How to join the items into a single string (default: newline).
        label: The label shown on the copy button (default: "Copy <column> list").
        transform: Optional function to transform each value before copying
                   (e.g., lambda x: x.lower()).
    """
    # If DataFrame is empty or the column doesn't exist, show a friendly message
    if df is None or column not in df.columns:
        st.info(f"Nothing to copy. Column `{column}` not found.")
        return

    # Convert the column to strings and store as a list
    items: Iterable[str] = df[column].astype(str).tolist()

    # Optionally transform each value before joining
    if transform:
        items = [transform(x) for x in items]

    # Join all items into one big string
    text = delimiter.join(items)

    # Reuse the base copy-to-clipboard function
    render_copy_to_clipboard(text, label or f"Copy {column} list")
