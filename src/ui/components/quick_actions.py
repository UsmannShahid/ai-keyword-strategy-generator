"""
Quick Actions Component
Provides sidebar shortcuts to jump to any step with smart defaults
"""

import streamlit as st
from typing import Optional


def show_keyword_input_modal(context: str) -> Optional[str]:
    """Show a modal for keyword input with context-specific guidance"""
    
    with st.expander(f"🔑 Enter keyword for {context}", expanded=True):
        # Recent keywords from session state
        recent_keywords = []
        if st.session_state.get("selected_keyword"):
            recent_keywords.append(st.session_state["selected_keyword"])
        
        # Keywords from recent sessions (we'll implement this later)
        # recent_keywords.extend(get_recent_keywords_from_db())
        
        # Show recent keywords if available
        if recent_keywords:
            selected_recent = st.selectbox(
                "Recent keywords:",
                [""] + recent_keywords,
                key=f"recent_{context}"
            )
            if selected_recent:
                return selected_recent
        
        # Manual keyword input
        manual_keyword = st.text_input(
            "Or enter any keyword:",
            placeholder="e.g., best yoga mats, SEO tips, etc.",
            key=f"manual_{context}"
        )
        
        if manual_keyword.strip():
            return manual_keyword.strip()
    
    return None


def render_quick_actions():
    """Render quick action buttons in the sidebar"""
    
    st.sidebar.markdown("### ⚡ Quick Actions")
    st.sidebar.markdown("Jump to any step instantly:")
    
    # Quick Brief Generation
    with st.sidebar:
        if st.button("📝 Generate Brief Now", use_container_width=True):
            keyword = show_keyword_input_modal("brief generation")
            if keyword:
                st.session_state.selected_keyword = keyword
                st.session_state.keyword_source = "quick_action"
                from ...core.state_manager import state_manager
                state_manager.go_to_step(3)
                st.rerun()
    
    # Quick SERP Analysis
    with st.sidebar:
        if st.button("🔍 Analyze SERP Now", use_container_width=True):
            keyword = show_keyword_input_modal("SERP analysis")
            if keyword:
                st.session_state.selected_keyword = keyword
                st.session_state.keyword_source = "quick_action"
                from ...core.state_manager import state_manager
                state_manager.go_to_step(4)
                st.rerun()
    
    # Quick Strategy Generation
    with st.sidebar:
        if st.button("💡 Get Strategy Now", use_container_width=True):
            keyword = show_keyword_input_modal("strategy generation")
            if keyword:
                st.session_state.selected_keyword = keyword
                st.session_state.keyword_source = "quick_action"
                from ...core.state_manager import state_manager
                state_manager.go_to_step(5)
                st.rerun()
    
    st.sidebar.markdown("---")
    
    # Current session info
    if st.session_state.get("selected_keyword"):
        st.sidebar.markdown("### 🎯 Current Session")
        st.sidebar.info(f"**Keyword:** {st.session_state['selected_keyword']}")
        
        current_step = st.session_state.get("ux_step", 1)
        step_names = {1: "Business Input", 2: "Keywords", 3: "Brief", 4: "SERP", 5: "Strategy"}
        st.sidebar.info(f"**Current Step:** {current_step} - {step_names.get(current_step, 'Unknown')}")
    
    # Reset session option
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Start New Session", use_container_width=True):
        # Clear session state but keep important data
        important_keys = ["seed_input", "industry_input", "audience_input", "country_input", "language_input"]
        session_backup = {key: st.session_state.get(key) for key in important_keys}
        
        st.session_state.clear()
        
        # Restore important data
        for key, value in session_backup.items():
            if value:
                st.session_state[key] = value
        
        from ...core.state_manager import state_manager
        state_manager.go_to_step(1)
        st.rerun()


def render_step_shortcuts():
    """Render quick shortcuts to specific steps"""
    
    st.sidebar.markdown("### 🚀 Step Shortcuts")
    
    current_step = st.session_state.get("ux_step", 1)
    
    # Only show shortcuts to accessible steps
    shortcuts = []
    
    # Step 1 is always accessible
    if current_step != 1:
        shortcuts.append(("🧭 Business Input", 1))
    
    # Step 2 if business input exists
    if st.session_state.get("seed_input", "").strip() and current_step != 2:
        shortcuts.append(("🔎 Keywords", 2))
    
    # Steps 3+ if keyword exists
    if st.session_state.get("selected_keyword", "").strip():
        if current_step != 3:
            shortcuts.append(("📝 Brief", 3))
        if current_step != 4:
            shortcuts.append(("🔍 SERP", 4))
        if current_step != 5:
            shortcuts.append(("💡 Strategy", 5))
    
    # Render shortcut buttons
    for label, step_num in shortcuts:
        if st.sidebar.button(label, use_container_width=True, key=f"shortcut_{step_num}"):
            from ...core.state_manager import state_manager
            state_manager.go_to_step(step_num)
            st.rerun()


def render_enhanced_sidebar():
    """Render the complete enhanced sidebar with all quick actions"""
    
    # Quick actions for jumping with keyword input
    render_quick_actions()
    
    # Step shortcuts for existing data
    render_step_shortcuts()


if __name__ == "__main__":
    # Test the component
    st.set_page_config(page_title="Quick Actions Test")
    render_enhanced_sidebar()
