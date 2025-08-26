"""
Data Manager Component
Handles smart caching, dependency checking, and data lifecycle management
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
from datetime import datetime, timedelta
from ...utils.db_utils import safe_get_full_session_data
from ...core.cache_manager import cache_manager


class DataDependencyManager:
    """Manages data dependencies and checks what data is available vs needed"""
    
    STEP_DEPENDENCIES = {
        1: [],                                    # Business input - no dependencies
        2: ["business_input"],                    # Keywords - needs business input
        3: ["keyword"],                          # Brief - needs keyword
        4: ["keyword"],                          # SERP - needs keyword (brief optional but helpful)
        5: ["keyword", "brief"]                  # Strategy - needs keyword and brief (SERP optional)
    }
    
    @staticmethod
    def get_step_requirements(step_number: int) -> List[str]:
        """Get required data for a specific step"""
        return DataDependencyManager.STEP_DEPENDENCIES.get(step_number, [])
    
    @staticmethod
    def check_data_availability(keyword: str = None) -> Dict[str, bool]:
        """Check what data is currently available"""
        current_keyword = keyword or st.session_state.get("selected_keyword", "")
        
        availability = {
            "business_input": bool(st.session_state.get("seed_input", "").strip()),
            "keyword": bool(current_keyword.strip()),
            "keywords_data": bool(st.session_state.get("keywords_data")),
            "brief": bool(st.session_state.get("brief_output")),
            "serp": bool(st.session_state.get("serp_data")),
            "suggestions": bool(st.session_state.get("ai_suggestions")),
            "session_id": bool(st.session_state.get("current_session_id"))
        }
        
        return availability
    
    @staticmethod
    def get_missing_dependencies(target_step: int, keyword: str = None) -> Tuple[List[str], List[str]]:
        """
        Check what dependencies are missing vs available for a target step
        
        Returns:
            Tuple of (missing_data, available_data)
        """
        requirements = DataDependencyManager.get_step_requirements(target_step)
        availability = DataDependencyManager.check_data_availability(keyword)
        
        missing_data = []
        available_data = []
        
        for req in requirements:
            if availability.get(req, False):
                available_data.append(req)
            else:
                missing_data.append(req)
        
        return missing_data, available_data
    
    @staticmethod
    def can_execute_step(step_number: int, keyword: str = None) -> bool:
        """Check if a step can be executed with current data"""
        missing_data, _ = DataDependencyManager.get_missing_dependencies(step_number, keyword)
        return len(missing_data) == 0
    
    @staticmethod
    def suggest_next_action(current_step: int = None) -> Dict[str, Any]:
        """Suggest what the user should do next based on available data"""
        if current_step is None:
            current_step = st.session_state.get("ux_step", 1)
        
        availability = DataDependencyManager.check_data_availability()
        
        suggestions = {
            "next_step": None,
            "can_skip_to": [],
            "missing_for_completion": [],
            "recommendations": []
        }
        
        # Find the furthest step we can reach
        for step in range(1, 6):
            if DataDependencyManager.can_execute_step(step):
                if step > current_step:
                    suggestions["can_skip_to"].append(step)
                if suggestions["next_step"] is None and step > current_step:
                    suggestions["next_step"] = step
        
        # Check what's missing for full completion
        missing_for_final, _ = DataDependencyManager.get_missing_dependencies(5)
        suggestions["missing_for_completion"] = missing_for_final
        
        # Generate recommendations
        if not availability["keyword"]:
            suggestions["recommendations"].append("Select a keyword to unlock brief generation")
        elif not availability["brief"]:
            suggestions["recommendations"].append("Generate a content brief to unlock strategy suggestions")
        elif not availability["serp"]:
            suggestions["recommendations"].append("Analyze SERP data for complete competitive insights")
        else:
            suggestions["recommendations"].append("All core data available - generate complete strategy!")
        
        return suggestions


class SmartCacheManager:
    """Manages intelligent caching of generated data"""
    
    @staticmethod
    def generate_cache_key(data_type: str, keyword: str, **params) -> str:
        """Generate a unique cache key for data"""
        # Include relevant parameters that affect the output
        cache_params = {
            "keyword": keyword.lower().strip(),
            "data_type": data_type,
            **params
        }
        
        # For brief generation, include variant
        if data_type == "brief":
            cache_params["variant"] = params.get("variant", "A")
        
        # For SERP, include location and language
        if data_type == "serp":
            cache_params["country"] = params.get("country", "US")
            cache_params["language"] = params.get("language", "en")
        
        # Create hash of parameters
        cache_string = json.dumps(cache_params, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()[:12]
        
        return f"{data_type}_{cache_hash}"
    
    @staticmethod
    def is_cache_valid(cached_data: Dict, max_age_hours: int = 24) -> bool:
        """Check if cached data is still valid"""
        if not cached_data or "timestamp" not in cached_data:
            return False
        
        try:
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            age = datetime.now() - cache_time
            return age < timedelta(hours=max_age_hours)
        except:
            return False
    
    @staticmethod
    def get_cached_data(data_type: str, keyword: str, **params) -> Optional[Dict]:
        """Get cached data if available and valid"""
        cache_key = SmartCacheManager.generate_cache_key(data_type, keyword, **params)
        
        # Check session state cache first (fastest)
        if cache_key in st.session_state:
            cached = st.session_state[cache_key]
            if SmartCacheManager.is_cache_valid(cached):
                return cached
        
        # Check database cache (persistent across sessions)
        try:
            # This would integrate with your database caching system
            # For now, return None as we don't have persistent cache implemented
            pass
        except:
            pass
        
        return None
    
    @staticmethod
    def cache_data(data_type: str, keyword: str, data: Any, **params):
        """Cache data for future use"""
        cache_key = SmartCacheManager.generate_cache_key(data_type, keyword, **params)
        
        cached_entry = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "data_type": data_type,
            "params": params
        }
        
        # Store in session state cache
        st.session_state[cache_key] = cached_entry
        
        # Optionally store in database cache for persistence
        # This would integrate with your database system
    
    @staticmethod
    def clear_cache_for_keyword(keyword: str):
        """Clear all cached data for a specific keyword"""
        keys_to_remove = []
        for key in st.session_state.keys():
            if isinstance(key, str) and key.startswith(("brief_", "serp_", "suggestions_")):
                cached_entry = st.session_state.get(key)
                if isinstance(cached_entry, dict) and cached_entry.get("keyword", "").lower() == keyword.lower():
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]


def get_or_generate_data(data_type: str, keyword: str, force_refresh: bool = False, **params) -> Tuple[Any, bool]:
    """
    Smart data retrieval - uses cache when possible, generates when needed
    
    Returns:
        Tuple of (data, was_cached)
    """
    
    if not force_refresh:
        # Try to get cached data first
        cached_data = SmartCacheManager.get_cached_data(data_type, keyword, **params)
        if cached_data:
            return cached_data["data"], True
    
    # Generate new data
    new_data = None
    
    if data_type == "brief":
        from ...core.services import generate_brief_with_variant
        variant = params.get("variant", "A")
        output, prompt, latency, usage = generate_brief_with_variant(keyword=keyword, variant=variant)
        new_data = {
            "output": output,
            "prompt": prompt,
            "latency": latency,
            "usage": usage,
            "variant": variant
        }
        
        # Update session state
        st.session_state.brief_output = output
        st.session_state.brief_variant = variant
        st.session_state.brief_latency = latency
        st.session_state.brief_usage = usage
    
    elif data_type == "serp":
        from ...core.services import fetch_serp_snapshot
        country = params.get("country", st.session_state.get("country_input", "US"))
        language = params.get("language", st.session_state.get("language_input", "en"))
        
        serp_data = fetch_serp_snapshot(keyword=keyword, country=country, language=language)
        new_data = serp_data
        
        # Update session state
        if serp_data:
            st.session_state.serp_data = serp_data
    
    elif data_type == "suggestions":
        # Generate AI suggestions based on keyword
        suggestions = generate_ai_suggestions(keyword)
        new_data = suggestions
        
        # Update session state
        st.session_state.ai_suggestions = suggestions
        st.session_state.ai_suggestions_generated = True
    
    # Cache the new data
    if new_data:
        SmartCacheManager.cache_data(data_type, keyword, new_data, **params)
    
    return new_data, False


def generate_ai_suggestions(keyword: str) -> Dict[str, str]:
    """Generate AI strategy suggestions for a keyword"""
    quick_wins = f"""**Quick-Win Opportunities for "{keyword}":**

🚀 **Immediate Actions:**
• Target long-tail variations: "{keyword} guide", "{keyword} tips", "best {keyword}"
• Create FAQ sections addressing common {keyword} questions
• Optimize for featured snippet opportunities with structured data
• Add comparison tables if competitors lack them

📈 **Content Gaps to Fill:**
• Update outdated information in competitor {keyword} content
• Add missing multimedia (images, videos, infographics) about {keyword}
• Create more comprehensive {keyword} guides
• Address specific user pain points related to {keyword}"""

    content_ideas = f"""**Content Ideas for "{keyword}":**

📝 **Primary Content:**
• Ultimate guide to {keyword}
• {keyword}: Beginner's complete tutorial  
• Common {keyword} mistakes to avoid
• {keyword} best practices and tips

🔄 **Supporting Content:**
• {keyword} vs alternatives comparison
• {keyword} case studies and examples
• {keyword} tools and resources roundup
• How to choose the right {keyword}

🎥 **Multimedia Opportunities:**
• Step-by-step {keyword} video tutorial
• {keyword} infographic or cheat sheet
• Interactive {keyword} calculator or tool
• {keyword} before/after showcase"""

    technical_seo = f"""**Technical SEO Checklist for "{keyword}":**

✅ **On-Page Optimization:**
• Include "{keyword}" in title tag (front-loaded)
• Use "{keyword}" in H1 and at least one H2
• Add "{keyword}" to meta description naturally
• Include related keywords: "{keyword} guide", "{keyword} tips"

✅ **User Experience:**
• Ensure fast page load speed (<3 seconds)
• Make {keyword} content mobile-friendly
• Add clear navigation and internal links
• Include table of contents for long {keyword} content

✅ **Content Structure:**
• Use proper heading hierarchy (H1 > H2 > H3)
• Add schema markup for {keyword} content
• Include relevant {keyword} images with alt text
• Create engaging meta descriptions about {keyword}"""

    return {
        "quick_wins": quick_wins,
        "content_ideas": content_ideas,
        "technical_seo": technical_seo
    }


def render_data_status_widget():
    """Render a widget showing current data status and cache information"""
    st.sidebar.markdown("### 📊 Data Status")
    
    current_keyword = st.session_state.get("selected_keyword", "")
    if not current_keyword:
        st.sidebar.info("No keyword selected")
        return
    
    st.sidebar.markdown(f"**Keyword:** `{current_keyword}`")
    
    # Check what data is available
    availability = DataDependencyManager.check_data_availability()
    
    status_icons = {
        True: "✅",
        False: "⏳"
    }
    
    data_labels = {
        "brief": "Content Brief",
        "serp": "SERP Analysis", 
        "suggestions": "AI Suggestions"
    }
    
    for data_type in ["brief", "serp", "suggestions"]:
        has_data = availability.get(data_type, False)
        icon = status_icons[has_data]
        label = data_labels[data_type]
        
        # Check if we have cached data
        cached_data = SmartCacheManager.get_cached_data(data_type, current_keyword)
        cache_indicator = " 💾" if cached_data else ""
        
        st.sidebar.markdown(f"{icon} {label}{cache_indicator}")
    
    # Show suggested next actions
    suggestions = DataDependencyManager.suggest_next_action()
    
    if suggestions["recommendations"]:
        st.sidebar.markdown("**💡 Suggestions:**")
        for rec in suggestions["recommendations"]:
            st.sidebar.caption(f"• {rec}")


if __name__ == "__main__":
    # Test the component
    st.set_page_config(page_title="Data Manager Test")
    
    st.title("Smart Data Manager Test")
    
    # Test dependency checking
    st.subheader("Dependency Check")
    availability = DataDependencyManager.check_data_availability()
    st.json(availability)
    
    # Test suggestions
    st.subheader("Next Action Suggestions") 
    suggestions = DataDependencyManager.suggest_next_action()
    st.json(suggestions)
    
    # Render sidebar widget
    render_data_status_widget()
