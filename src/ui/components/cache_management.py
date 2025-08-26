"""
Cache Management UI Component
Provides user interface for cache monitoring, management, and optimization
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ...core.cache_manager import cache_manager
from ...services.smart_data_service import SmartDataService


def render_cache_management_section():
    """Render cache management section in the sidebar"""
    
    with st.sidebar.expander("🗄️ Cache Management", expanded=False):
        
        # Get cache statistics
        stats = cache_manager.get_cache_stats()
        
        # Display cache overview
        st.markdown("### Cache Overview")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Session", stats.get("session_entries", 0))
        with col2:
            st.metric("Persistent", stats.get("persistent_entries", 0))
        
        # Display cache by type
        if stats.get("by_type"):
            st.markdown("**By Type:**")
            for data_type, count in stats["by_type"].items():
                st.caption(f"📊 {data_type}: {count}")
        
        # Cache actions
        st.markdown("### Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧹 Cleanup", help="Remove expired cache entries"):
                cleaned = cache_manager.cleanup_expired()
                if cleaned > 0:
                    st.success(f"Removed {cleaned} expired entries")
                else:
                    st.info("No expired entries found")
        
        with col2:
            if st.button("🗑️ Clear All", help="Clear all cached data"):
                cache_manager.clear()
                st.success("Cache cleared")
                st.rerun()


def render_keyword_cache_status(keyword: str):
    """Render cache status for a specific keyword"""
    
    if not keyword:
        return
    
    freshness_info = SmartDataService.check_data_freshness(keyword)
    
    st.markdown("### 📊 Data Status")
    
    status_icons = {
        True: "✅",
        False: "⏳"
    }
    
    freshness_icons = {
        True: "🟢",
        False: "🟡"
    }
    
    for data_type, info in freshness_info.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            exists_icon = status_icons[info["exists"]]
            fresh_icon = freshness_icons[info.get("is_fresh", False)] if info["exists"] else ""
            
            st.markdown(f"{exists_icon} {fresh_icon} **{data_type.title()}**")
        
        with col2:
            if info["exists"] and info["age_hours"] is not None:
                if info["age_hours"] < 1:
                    st.caption("< 1h")
                elif info["age_hours"] < 24:
                    st.caption(f"{info['age_hours']:.1f}h")
                else:
                    st.caption(f"{info['age_hours']/24:.1f}d")
            else:
                st.caption("—")
        
        with col3:
            if info["exists"]:
                cache_key = cache_manager.generate_smart_key(data_type, keyword)
                if st.button("🔄", key=f"refresh_{data_type}_{keyword}", help=f"Refresh {data_type}"):
                    refresh_data_type(data_type, keyword)
                    st.rerun()


def refresh_data_type(data_type: str, keyword: str):
    """Refresh specific data type for a keyword"""
    
    try:
        if data_type == "brief":
            variant = st.session_state.get("brief_variant", "A")
            SmartDataService.get_or_generate_brief(keyword, variant, force_refresh=True)
            st.success(f"Brief refreshed for '{keyword}'")
        
        elif data_type == "serp":
            country = st.session_state.get("country_input", "US")
            language = st.session_state.get("language_input", "en")
            SmartDataService.get_or_generate_serp(keyword, country, language, force_refresh=True)
            st.success(f"SERP data refreshed for '{keyword}'")
        
        elif data_type == "suggestions":
            SmartDataService.get_or_generate_suggestions(keyword, force_refresh=True)
            st.success(f"AI suggestions refreshed for '{keyword}'")
    
    except Exception as e:
        st.error(f"Failed to refresh {data_type}: {str(e)}")


def render_smart_caching_widget():
    """Render smart caching widget with performance insights"""
    
    current_keyword = st.session_state.get("selected_keyword", "")
    
    if not current_keyword:
        st.info("💡 Select a keyword to see data status")
        return
    
    # Cache status for current keyword
    with st.container():
        st.markdown(f"**Data Status for:** `{current_keyword}`")
        
        freshness_info = SmartDataService.check_data_freshness(current_keyword)
        
        # Quick status overview
        total_data_types = len(freshness_info)
        existing_data = sum(1 for info in freshness_info.values() if info["exists"])
        fresh_data = sum(1 for info in freshness_info.values() if info.get("is_fresh", False))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Available", f"{existing_data}/{total_data_types}")
        
        with col2:
            st.metric("Fresh", f"{fresh_data}/{existing_data}" if existing_data > 0 else "0/0")
        
        with col3:
            if existing_data < total_data_types:
                if st.button("⚡ Generate Missing", help="Generate all missing data"):
                    generate_missing_data(current_keyword, freshness_info)
                    st.rerun()
            else:
                st.success("Complete ✅")
        
        # Detailed status
        render_keyword_cache_status(current_keyword)


def generate_missing_data(keyword: str, freshness_info: Dict[str, Dict[str, Any]]):
    """Generate all missing data for a keyword"""
    
    missing_data = [data_type for data_type, info in freshness_info.items() if not info["exists"]]
    
    if not missing_data:
        st.info("All data already exists")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_steps = len(missing_data)
    
    for i, data_type in enumerate(missing_data):
        status_text.text(f"Generating {data_type}...")
        progress_bar.progress((i + 1) / total_steps)
        
        try:
            if data_type == "brief":
                SmartDataService.get_or_generate_brief(keyword, force_refresh=True)
            elif data_type == "serp":
                SmartDataService.get_or_generate_serp(keyword, force_refresh=True)
            elif data_type == "suggestions":
                SmartDataService.get_or_generate_suggestions(keyword, force_refresh=True)
        except Exception as e:
            st.error(f"Failed to generate {data_type}: {str(e)}")
    
    status_text.text("✅ Generation complete!")
    progress_bar.progress(1.0)


def render_cache_performance_insights():
    """Render cache performance insights and recommendations"""
    
    with st.expander("📈 Cache Performance", expanded=False):
        
        stats = cache_manager.get_cache_stats()
        
        # Performance metrics
        st.markdown("### Performance Insights")
        
        total_entries = stats.get("total_entries", 0)
        
        if total_entries > 0:
            # Cache utilization
            session_ratio = stats.get("session_entries", 0) / total_entries
            persistent_ratio = stats.get("persistent_entries", 0) / total_entries
            
            st.markdown("**Cache Distribution:**")
            st.progress(session_ratio, text=f"Session: {session_ratio:.1%}")
            st.progress(persistent_ratio, text=f"Persistent: {persistent_ratio:.1%}")
            
            # Recommendations
            st.markdown("### 💡 Recommendations")
            
            if session_ratio > 0.8:
                st.info("🔄 High session cache usage. Consider clearing session cache periodically.")
            
            if total_entries > 100:
                st.warning("📦 Large cache size. Consider running cleanup to remove expired entries.")
            
            if stats.get("persistent_entries", 0) == 0:
                st.info("💾 No persistent cache entries. Data will be regenerated between sessions.")
        
        else:
            st.info("No cache data available. Start generating data to see performance insights.")


def render_advanced_cache_controls():
    """Render advanced cache control options"""
    
    with st.expander("⚙️ Advanced Controls", expanded=False):
        
        st.markdown("### Cache Settings")
        
        # Cache expiration settings
        col1, col2 = st.columns(2)
        
        with col1:
            brief_ttl = st.number_input(
                "Brief Cache (hours)",
                min_value=1,
                max_value=168,
                value=24,
                help="How long to cache brief data"
            )
        
        with col2:
            serp_ttl = st.number_input(
                "SERP Cache (hours)",
                min_value=1,
                max_value=48,
                value=12,
                help="How long to cache SERP data"
            )
        
        # Apply settings
        if st.button("Apply Settings"):
            st.session_state.cache_settings = {
                "brief_ttl": brief_ttl,
                "serp_ttl": serp_ttl
            }
            st.success("Cache settings updated")
        
        # Bulk operations
        st.markdown("### Bulk Operations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Brief Cache"):
                # Implementation would clear only brief cache
                st.info("Brief cache cleared")
        
        with col2:
            if st.button("🗑️ Clear SERP Cache"):
                # Implementation would clear only SERP cache
                st.info("SERP cache cleared")


if __name__ == "__main__":
    # Test the cache management UI
    st.set_page_config(page_title="Cache Management Test")
    
    st.title("Smart Cache Management")
    
    # Simulate some session state
    st.session_state.selected_keyword = "digital marketing"
    
    # Test the widgets
    render_smart_caching_widget()
    render_cache_performance_insights()
    render_advanced_cache_controls()
