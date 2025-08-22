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
        <button onclick="copyToClipboard()" style="
            background: #3b82f6;
            color: white;
            border: 2px solid #2563eb;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
            transition: all 0.2s ease;
        " onmouseover="this.style.background='#2563eb'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(59, 130, 246, 0.3)'"
           onmouseout="this.style.background='#3b82f6'; this.style.transform='translateY(0px)'; this.style.boxShadow='0 2px 4px rgba(59, 130, 246, 0.2)'"
        >
            📋 {label}
        </button>
        
        <script>
        function copyToClipboard() {{
            const text = {payload};
            navigator.clipboard.writeText(text).then(function() {{
                // Create and show toast
                const toast = document.createElement('div');
                toast.innerHTML = '✅ Copied!';
                toast.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    z-index: 9999;
                    font-weight: 500;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    animation: slideIn 0.3s ease-out;
                `;
                document.body.appendChild(toast);
                
                // Remove toast after 2 seconds
                setTimeout(() => {{
                    toast.style.animation = 'slideOut 0.3s ease-in';
                    setTimeout(() => document.body.removeChild(toast), 300);
                }}, 2000);
            }}).catch(function(err) {{
                console.error('Failed to copy: ', err);
            }});
        }}
        </script>
        
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes slideOut {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
        </style>
        """,
        height=50,
    )


def render_copy_from_dataframe(df, label="Copy table as CSV"):
    """
    Convert DataFrame to CSV and add a copy button.
    """
    if df is None or df.empty:
        st.warning("No data to copy")
        return
    
    csv_text = df.to_csv(index=False)
    render_copy_to_clipboard(csv_text, label)