"""
Step Navigator Component
Provides visual progress indicator and allows jumping between steps
"""

import streamlit as st
from typing import Dict, List, Optional
from ...core.state_manager import state_manager


def get_step_status(step_number: int, current_step: int) -> str:
    """Get the status of a step (completed, current, pending)"""
    if step_number < current_step:
        return "completed"
    elif step_number == current_step:
        return "current"
    else:
        return "pending"


def can_access_step(step_number: int) -> bool:
    """Check if user can access a specific step"""
    # Step 1 is always accessible
    if step_number == 1:
        return True
    
    # Step 2 requires business input
    if step_number == 2:
        return bool(st.session_state.get("seed_input", "").strip())
    
    # Steps 3+ require a selected keyword
    if step_number >= 3:
        return bool(st.session_state.get("selected_keyword", "").strip())
    
    return False


def get_step_info() -> List[Dict]:
    """Get information about all steps"""
    return [
        {
            "number": 1,
            "title": "Business",
            "icon": "🧭",
            "description": "Describe your business",
            "required_data": []
        },
        {
            "number": 2,
            "title": "Keywords",
            "icon": "🔎",
            "description": "Choose target keyword",
            "required_data": ["business_input"]
        },
        {
            "number": 3,
            "title": "Brief",
            "icon": "📝",
            "description": "Generate content brief",
            "required_data": ["keyword"]
        },
        {
            "number": 4,
            "title": "SERP",
            "icon": "🔍",
            "description": "Analyze competition",
            "required_data": ["keyword"]
        },
        {
            "number": 5,
            "title": "Strategy",
            "icon": "💡",
            "description": "AI recommendations",
            "required_data": ["keyword", "brief"]
        }
    ]


def render_step_navigator():
    """Render the horizontal step navigator"""
    current_step = st.session_state.get("ux_step", 1)
    steps = get_step_info()
    
    st.markdown("### 🧭 Navigation")
    
    # Create columns for each step
    cols = st.columns(len(steps))
    
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            step_num = step["number"]
            status = get_step_status(step_num, current_step)
            can_access = can_access_step(step_num)
            
            # Choose styling based on status
            if status == "completed":
                icon_style = "✅"
                button_type = "secondary"
                disabled = False
            elif status == "current":
                icon_style = "🔄"
                button_type = "primary"
                disabled = False
            else:
                icon_style = "⏳"
                button_type = "secondary"
                disabled = not can_access
            
            # Step button
            button_label = f"{icon_style} {step['icon']}\n{step['title']}"
            
            if st.button(
                button_label,
                key=f"nav_step_{step_num}",
                type=button_type,
                disabled=disabled,
                use_container_width=True,
                help=step['description'] if can_access else f"Complete previous steps to unlock"
            ):
                if can_access:
                    state_manager.go_to_step(step_num)
                    st.rerun()
    
    # Show current step info
    current_step_info = next(s for s in steps if s["number"] == current_step)
    st.info(f"**Current:** {current_step_info['icon']} {current_step_info['title']} - {current_step_info['description']}")


def render_progress_bar():
    """Render a simple progress bar"""
    current_step = st.session_state.get("ux_step", 1)
    total_steps = 5
    
    progress = (current_step - 1) / (total_steps - 1)
    st.progress(progress)
    st.caption(f"Step {current_step} of {total_steps}")


def render_step_breadcrumb():
    """Render breadcrumb navigation"""
    current_step = st.session_state.get("ux_step", 1)
    steps = get_step_info()
    
    breadcrumb_items = []
    
    for step in steps:
        step_num = step["number"]
        
        if step_num < current_step:
            # Completed step - make it clickable
            if can_access_step(step_num):
                breadcrumb_items.append(f"[{step['icon']} {step['title']}](#)")
            else:
                breadcrumb_items.append(f"{step['icon']} {step['title']}")
        elif step_num == current_step:
            # Current step - highlight
            breadcrumb_items.append(f"**{step['icon']} {step['title']}**")
        else:
            # Future step
            breadcrumb_items.append(f"{step['icon']} {step['title']}")
    
    st.markdown(" → ".join(breadcrumb_items))


if __name__ == "__main__":
    # Test the component
    st.set_page_config(page_title="Navigation Test")
    render_step_navigator()
