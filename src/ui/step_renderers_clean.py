"""
Step Renderers for the AI Keyword Tool
Enhanced with navigation, smart caching, and improved data management - Clean Version
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import time

# Import navigation and UI components
from .components.step_navigator import render_step_navigator
from .components.quick_actions import render_enhanced_sidebar
from .components.keyword_selector import render_keyword_selector
from .components.cache_management import render_smart_caching_widget, render_cache_management_section

# Import smart data services
from ..services.smart_data_service import SmartDataService
from ..core.cache_manager import cache_manager
from ..core.services import (
    generate_keywords_from_seed,
    generate_brief_with_variant,
    fetch_serp_snapshot,
    generate_suggestions_with_llm,
    save_session_to_db
)
from ..utils.db_utils import (
    save_keyword_extraction_to_db,
    get_recent_keyword_extractions,
    safe_get_full_session_data,
    get_recent_keyword_extractions_with_data
)

# Import state manager
try:
    from ..core.state_manager import state_manager
except ImportError:
    # Create a simple state manager if not available
    class SimpleStateManager:
        def go_to_step(self, step: int):
            st.session_state.ux_step = step
    state_manager = SimpleStateManager()


def render_current_step():
    """Render the current step with enhanced navigation and smart caching"""
    
    # Render enhanced sidebar with navigation and cache management
    render_enhanced_sidebar()
    render_cache_management_section()
    
    # Render step navigator
    render_step_navigator()
    
    # Add cache status widget if keyword is selected
    current_keyword = st.session_state.get("selected_keyword", "")
    if current_keyword:
        with st.sidebar:
            render_smart_caching_widget()
    
    # Get current step
    current_step = st.session_state.get("ux_step", 1)
    
    # Render appropriate step
    if current_step == 1:
        render_step_1_business_input()
    elif current_step == 2:
        render_step_2_keywords()
    elif current_step == 3:
        render_step_3_brief()
    elif current_step == 4:
        render_step_4_serp()
    elif current_step == 5:
        render_step_5_suggestions()
    else:
        st.error(f"Invalid step: {current_step}")
        st.session_state.ux_step = 1


def render_step_1_business_input():
    """Render step 1: Business input and context setting"""
    st.markdown("### 🏢 Step 1: Business Context")
    st.info("Provide context about your business to generate targeted keyword suggestions.")
    
    seed_input = st.text_area(
        "Describe your business, product, or service:",
        value=st.session_state.get("seed_input", ""),
        height=100,
        placeholder="e.g., We provide digital marketing services for small businesses, focusing on SEO, social media management, and content creation."
    )
    
    st.session_state.seed_input = seed_input
    
    if seed_input.strip() and st.button("✨ Generate Keywords", type="primary"):
        state_manager.go_to_step(2)


def render_step_2_keywords():
    """Render step 2: Keyword generation and selection"""
    st.markdown("### 🔑 Step 2: Keyword Selection")
    
    # Universal keyword selector
    keyword = render_keyword_selector(
        context="keyword_generation",
        help_text="Select a keyword or generate new ones from your business description",
        show_recent=True,
        show_generated=True,
        show_manual=True,
        show_smart_paste=True
    )
    
    if keyword and st.button("📝 Continue with this keyword", type="primary"):
        st.session_state.selected_keyword = keyword
        state_manager.go_to_step(3)


def render_step_3_brief():
    """Render step 3: Content brief generation with smart caching"""
    st.markdown("### 📝 Step 3: AI Content Brief")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected.")
        if st.button("← Back to Keywords"):
            state_manager.go_to_step(2)
        return
    
    st.info(f"**Selected keyword:** {selected_kw}")
    
    # Variant selection
    variant = st.radio("Choose variant:", ["A", "B"], horizontal=True)
    
    # Smart caching indicator
    freshness_info = SmartDataService.check_data_freshness(selected_kw)
    brief_info = freshness_info.get("brief", {})
    
    use_cached = False
    if brief_info.get("exists", False) and brief_info.get("is_fresh", False):
        st.success(f"✨ Fresh brief available (generated {brief_info.get('age_hours', 0):.1f}h ago)")
        use_cached = st.checkbox("Use cached brief", value=True)
    elif brief_info.get("exists", False):
        st.info(f"⏰ Cached brief available but older ({brief_info.get('age_hours', 0):.1f}h)")
    
    if st.button("🚀 Generate Content Brief", type="primary"):
        with st.spinner("Generating content brief..."):
            brief_data, was_cached = SmartDataService.get_or_generate_brief(
                keyword=selected_kw,
                variant=variant,
                force_refresh=not use_cached
            )
            
            if "error" in brief_data:
                st.error(f"Error: {brief_data['error']}")
            else:
                if was_cached:
                    st.success("✨ Loaded from cache")
                else:
                    st.success("✅ Brief generated successfully")
    
    # Display brief
    if st.session_state.get("brief_output"):
        st.markdown("#### Generated Brief")
        st.markdown(st.session_state.brief_output)
        
        if st.button("🔍 Continue to SERP Analysis", type="primary"):
            state_manager.go_to_step(4)


def render_step_4_serp():
    """Render step 4: SERP analysis with smart caching"""
    st.markdown("### 🔍 Step 4: SERP Analysis")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected.")
        if st.button("← Back to Brief"):
            state_manager.go_to_step(3)
        return
    
    st.info(f"**Analyzing SERP for:** {selected_kw}")
    
    # Smart caching for SERP
    freshness_info = SmartDataService.check_data_freshness(selected_kw)
    serp_info = freshness_info.get("serp", {})
    
    use_cached = False
    if serp_info.get("exists", False) and serp_info.get("is_fresh", False):
        st.success(f"✨ Fresh SERP data available (generated {serp_info.get('age_hours', 0):.1f}h ago)")
        use_cached = st.checkbox("Use cached SERP data", value=True)
    elif serp_info.get("exists", False):
        st.info(f"⏰ Cached SERP data available but older ({serp_info.get('age_hours', 0):.1f}h)")
    
    if not st.session_state.get("serp_data") or st.button("🔍 Fetch SERP Data"):
        with st.spinner("Fetching SERP data..."):
            serp_data, was_cached = SmartDataService.get_or_generate_serp(
                keyword=selected_kw,
                force_refresh=not use_cached
            )
            
            if serp_data:
                if was_cached:
                    st.success("✨ Loaded from cache")
                else:
                    st.success("✅ SERP data fetched successfully")
            else:
                st.error("Failed to fetch SERP data")
    
    # Display SERP results
    if st.session_state.get("serp_data"):
        st.markdown("#### 🏆 Top Competitors")
        
        serp_data = st.session_state.serp_data
        for i, result in enumerate(serp_data[:5], 1):
            with st.expander(f"{i}. {result.get('title', 'No title')[:60]}..."):
                st.write(f"**URL:** {result.get('url', 'N/A')}")
                st.write(f"**Snippet:** {result.get('snippet', 'N/A')}")
        
        if st.button("💡 Continue to Strategy", type="primary"):
            state_manager.go_to_step(5)


def render_step_5_suggestions():
    """Render step 5: Content suggestions with smart caching"""
    st.markdown("### 💡 Step 5: Content Strategy Suggestions")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected.")
        if st.button("← Back to SERP"):
            state_manager.go_to_step(4)
        return
    
    st.success(f"**Strategy for:** {selected_kw}")
    
    # Smart caching for suggestions
    freshness_info = SmartDataService.check_data_freshness(selected_kw)
    suggestions_info = freshness_info.get("suggestions", {})
    
    use_cached = False
    if suggestions_info.get("exists", False) and suggestions_info.get("is_fresh", False):
        st.success(f"✨ Fresh suggestions available (generated {suggestions_info.get('age_hours', 0):.1f}h ago)")
        use_cached = st.checkbox("Use cached suggestions", value=True)
    elif suggestions_info.get("exists", False):
        st.info(f"⏰ Cached suggestions available but older ({suggestions_info.get('age_hours', 0):.1f}h)")
    
    if not st.session_state.get("ai_suggestions_generated") or st.button("✨ Generate AI Suggestions"):
        with st.spinner("Generating content suggestions..."):
            suggestions_data, was_cached = SmartDataService.get_or_generate_suggestions(
                keyword=selected_kw,
                force_refresh=not use_cached
            )
            
            if "error" in suggestions_data:
                st.error(f"Error: {suggestions_data['error']}")
            else:
                if was_cached:
                    st.success("✨ Loaded from cache")
                else:
                    st.success("✅ Suggestions generated successfully")
    
    # Display suggestions
    ai_suggestions = st.session_state.get("ai_suggestions", {})
    if ai_suggestions:
        st.markdown("#### 🎯 AI-Generated Content Strategy")
        
        tabs = st.tabs(["Quick Wins", "Content Ideas", "Technical SEO", "Action Plan"])
        
        with tabs[0]:
            st.markdown(ai_suggestions.get("quick_wins", "No quick wins available."))
        
        with tabs[1]:
            st.markdown(ai_suggestions.get("content_ideas", "No content ideas available."))
        
        with tabs[2]:
            st.markdown(ai_suggestions.get("technical_seo", "No technical SEO suggestions available."))
        
        with tabs[3]:
            st.markdown(f"""
            ### 🚀 Your Action Plan for "{selected_kw}"
            
            1. **Content Creation Priority:**
               - Start with quick-win content opportunities
               - Create comprehensive guides that outrank competitors
               - Focus on gaps in competitor content
            
            2. **Technical Implementation:**
               - Apply all technical SEO recommendations
               - Ensure mobile-first design and fast loading
               - Implement structured data for featured snippets
            
            3. **Performance Monitoring:**
               - Track rankings for "{selected_kw}" and variations
               - Monitor competitor content updates
               - Measure user engagement and conversion rates
            """)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                from .helpers import generate_complete_strategy_export
                st.download_button(
                    "📥 Download Strategy",
                    data=generate_complete_strategy_export(selected_kw, ai_suggestions),
                    file_name=f"strategy_{selected_kw.replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with col2:
                if st.button("🔄 Start New Analysis", type="primary", use_container_width=True):
                    # Clear session and restart
                    for key in list(st.session_state.keys()):
                        if key not in ["dev_mode"]:
                            del st.session_state[key]
                    st.success("✅ Session cleared! Ready for new analysis.")
                    state_manager.go_to_step(1)
    else:
        st.info("💡 Generate suggestions above to see your content strategy.")


# Context tips renderer
def render_keyword_context_tips(context: str):
    """Render helpful context tips based on current step"""
    if context == "brief_generation":
        with st.expander("💡 Brief Generation Tips", expanded=False):
            st.markdown("""
            **Variant A** creates structured SEO briefs with technical details  
            **Variant B** creates writer-friendly formats with clear instructions  
            
            The AI will analyze your keyword and create a comprehensive content brief including:
            - Target audience analysis
            - Content structure recommendations  
            - SEO optimization guidelines
            - Competitive insights
            """)


# Helper functions
def safe_save_session(topic: str) -> Optional[str]:
    """Safely save session to database"""
    try:
        return save_session_to_db(topic)
    except Exception as e:
        print(f"Failed to save session: {e}")
        return None

def safe_save_brief(session_id: str, brief_content: str) -> bool:
    """Safely save brief to database"""
    try:
        # Implementation would go here
        return True
    except Exception as e:
        print(f"Failed to save brief: {e}")
        return False

def safe_save_serp(session_id: str, serp_data: str) -> bool:
    """Safely save SERP data to database"""
    try:
        # Implementation would go here  
        return True
    except Exception as e:
        print(f"Failed to save SERP: {e}")
        return False

def analyze_serp(serp_data: List[Dict]) -> Dict[str, Any]:
    """Analyze SERP data and return insights"""
    if not serp_data:
        return {"total_results": 0, "domains": [], "avg_title_length": 0}
    
    domains = list(set([result.get("url", "").split("/")[2] for result in serp_data]))
    avg_title_length = sum(len(result.get("title", "")) for result in serp_data) / len(serp_data)
    
    return {
        "total_results": len(serp_data),
        "domains": domains,
        "avg_title_length": avg_title_length
    }
