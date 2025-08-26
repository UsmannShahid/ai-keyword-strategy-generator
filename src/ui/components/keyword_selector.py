"""
Universal Keyword Selector Component
Provides flexible keyword input with multiple sources and context awareness
"""

import streamlit as st
from typing import List, Optional, Dict, Any
import json
from ...utils.db_utils import safe_get_recent_sessions


def get_recent_keywords_from_db(limit: int = 10) -> List[str]:
    """Get recent keywords from database sessions"""
    try:
        recent_sessions = safe_get_recent_sessions(limit=limit*2)  # Get more to filter unique keywords
        
        keywords = []
        seen_keywords = set()
        
        for session in recent_sessions:
            # Extract keyword from session topic or data
            if session.get('topic'):
                # Try to extract keyword from topic
                topic = session['topic']
                # Simple extraction - could be enhanced
                potential_keywords = [
                    topic.split(' - ')[-1] if ' - ' in topic else topic,
                    topic.split(':')[-1].strip() if ':' in topic else None
                ]
                
                for kw in potential_keywords:
                    if kw and kw.lower() not in seen_keywords and len(kw.strip()) > 2:
                        keywords.append(kw.strip())
                        seen_keywords.add(kw.lower())
                        if len(keywords) >= limit:
                            break
            
            if len(keywords) >= limit:
                break
        
        return keywords[:limit]
    
    except Exception as e:
        print(f"Error getting recent keywords: {e}")
        return []


def get_generated_keywords() -> List[str]:
    """Get keywords from current session's generated keywords"""
    keywords_data = st.session_state.get("keywords_data", {})
    
    all_keywords = []
    for category, kws in keywords_data.items():
        for kw in kws:
            if isinstance(kw, dict):
                all_keywords.append(kw["keyword"])
            else:
                all_keywords.append(str(kw))
    
    return all_keywords


def detect_keyword_from_text(text: str) -> Optional[str]:
    """Simple keyword detection from pasted text"""
    if not text or len(text.strip()) < 3:
        return None
    
    # Simple heuristics for keyword detection
    text = text.strip()
    
    # If it's a short phrase, likely a keyword
    if len(text.split()) <= 5 and len(text) <= 50:
        return text
    
    # Try to extract from URL
    if 'google.com/search' in text and 'q=' in text:
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(text)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                return query_params['q'][0]
        except:
            pass
    
    # Try to extract from title or first line
    lines = text.split('\n')
    first_line = lines[0].strip()
    if len(first_line.split()) <= 5 and len(first_line) <= 50:
        return first_line
    
    return None


def render_keyword_selector(
    context: str = "",
    required: bool = True,
    show_recent: bool = True,
    show_generated: bool = True,
    show_manual: bool = True,
    show_smart_paste: bool = True,
    default_value: str = "",
    help_text: str = ""
) -> Optional[str]:
    """
    Universal keyword selector with multiple input methods
    
    Args:
        context: Description of where this selector is used
        required: Whether a keyword selection is required
        show_recent: Show recent keywords from database
        show_generated: Show keywords from current generation
        show_manual: Show manual text input
        show_smart_paste: Show smart paste/clipboard detection
        default_value: Default value for manual input
        help_text: Additional help text to show
    
    Returns:
        Selected keyword or None
    """
    
    selected_keyword = None
    
    # Context header
    if context:
        st.markdown(f"**Select keyword for {context}:**")
    
    if help_text:
        st.info(help_text)
    
    # Option 1: Recent keywords from database
    if show_recent:
        recent_keywords = get_recent_keywords_from_db()
        if recent_keywords:
            st.markdown("##### 📚 Recent Keywords")
            
            # Show as selectbox or buttons based on count
            if len(recent_keywords) <= 5:
                # Show as buttons for easy clicking
                cols = st.columns(min(len(recent_keywords), 3))
                for i, keyword in enumerate(recent_keywords):
                    with cols[i % 3]:
                        if st.button(
                            f"🔑 {keyword}",
                            key=f"recent_btn_{context}_{i}",
                            use_container_width=True,
                            help=f"Use '{keyword}'"
                        ):
                            selected_keyword = keyword
                            st.session_state[f"keyword_source_{context}"] = "recent"
            else:
                # Show as selectbox for many keywords
                recent_selected = st.selectbox(
                    "Choose from recent:",
                    [""] + recent_keywords,
                    key=f"recent_select_{context}"
                )
                if recent_selected:
                    selected_keyword = recent_selected
                    st.session_state[f"keyword_source_{context}"] = "recent"
    
    # Option 2: Generated keywords from current session
    if show_generated and st.session_state.get("keywords_data"):
        generated_keywords = get_generated_keywords()
        if generated_keywords:
            st.markdown("##### 🎯 Generated Keywords")
            generated_selected = st.selectbox(
                "Choose from generated:",
                [""] + generated_keywords,
                key=f"generated_select_{context}"
            )
            if generated_selected:
                selected_keyword = generated_selected
                st.session_state[f"keyword_source_{context}"] = "generated"
    
    # Option 3: Smart paste/clipboard detection
    if show_smart_paste:
        st.markdown("##### 📋 Smart Paste")
        
        paste_text = st.text_area(
            "Paste text/URL and we'll extract the keyword:",
            placeholder="Paste Google search URL, article title, or any text...",
            height=60,
            key=f"paste_area_{context}"
        )
        
        if paste_text.strip():
            detected = detect_keyword_from_text(paste_text)
            if detected:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.success(f"✨ Detected keyword: **{detected}**")
                with col2:
                    if st.button("Use This", key=f"use_detected_{context}"):
                        selected_keyword = detected
                        st.session_state[f"keyword_source_{context}"] = "detected"
            else:
                st.warning("Couldn't detect a keyword. Try the manual input below.")
    
    # Option 4: Manual text input
    if show_manual:
        st.markdown("##### ✏️ Manual Entry")
        manual_keyword = st.text_input(
            "Enter any keyword:",
            value=default_value,
            placeholder="e.g., best yoga mats, SEO tips, digital marketing...",
            key=f"manual_input_{context}",
            help="Type any keyword or phrase you want to analyze"
        )
        
        if manual_keyword.strip():
            selected_keyword = manual_keyword.strip()
            st.session_state[f"keyword_source_{context}"] = "manual"
    
    # Show selected keyword confirmation
    if selected_keyword:
        source = st.session_state.get(f"keyword_source_{context}", "manual")
        source_icons = {
            "recent": "📚",
            "generated": "🎯", 
            "detected": "📋",
            "manual": "✏️"
        }
        
        st.success(f"{source_icons.get(source, '🔑')} **Selected:** {selected_keyword}")
        
        # Option to edit the selected keyword
        with st.expander("✏️ Edit selected keyword"):
            edited_keyword = st.text_input(
                "Modify keyword:",
                value=selected_keyword,
                key=f"edit_keyword_{context}"
            )
            if edited_keyword != selected_keyword and edited_keyword.strip():
                if st.button("Update Keyword", key=f"update_btn_{context}"):
                    selected_keyword = edited_keyword.strip()
                    st.session_state[f"keyword_source_{context}"] = "edited"
                    st.rerun()
    
    return selected_keyword


def render_keyword_history():
    """Render a sidebar widget showing keyword history"""
    st.sidebar.markdown("### 📚 Keyword History")
    
    recent_keywords = get_recent_keywords_from_db(limit=8)
    
    if recent_keywords:
        for i, keyword in enumerate(recent_keywords):
            if st.sidebar.button(
                f"🔑 {keyword[:25]}{'...' if len(keyword) > 25 else ''}",
                key=f"history_sidebar_{i}",
                use_container_width=True,
                help=f"Load keyword: {keyword}"
            ):
                st.session_state.selected_keyword = keyword
                st.session_state.keyword_source = "history"
                st.rerun()
    else:
        st.sidebar.info("No recent keywords found")


def render_keyword_context_tips(context: str):
    """Show context-specific tips for keyword selection"""
    tips = {
        "brief_generation": [
            "Use specific, descriptive keywords for better content briefs",
            "Long-tail keywords (3+ words) often produce more targeted content",
            "Include intent words like 'best', 'how to', 'guide' when relevant"
        ],
        "serp_analysis": [
            "Use exact match keywords to see real competition",
            "Try variations to see different SERP features",
            "Commercial keywords show more ads and competition"
        ],
        "strategy_generation": [
            "Broader keywords reveal more content opportunities", 
            "Try industry-specific terms for targeted strategies",
            "Consider seasonal or trending variations"
        ]
    }
    
    context_tips = tips.get(context, [])
    if context_tips:
        with st.expander("💡 Tips for this step"):
            for tip in context_tips:
                st.markdown(f"• {tip}")


if __name__ == "__main__":
    # Test the component
    st.set_page_config(page_title="Keyword Selector Test")
    
    st.title("Universal Keyword Selector Test")
    
    keyword = render_keyword_selector(
        context="testing",
        help_text="This is a test of the universal keyword selector"
    )
    
    if keyword:
        st.write(f"You selected: **{keyword}**")
    
    render_keyword_history()
