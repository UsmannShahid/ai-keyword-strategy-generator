"""
Smart Data Service
Intelligent data generation with caching, dependency tracking, and optimization
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..core.cache_manager import cache_manager
from ..core.services import (
    generate_brief_with_variant,
    fetch_serp_snapshot
)


class SmartDataService:
    """Service layer for intelligent data generation with caching"""
    
    @staticmethod
    def get_or_generate_brief(keyword: str, variant: str = "A", force_refresh: bool = False) -> Tuple[Dict[str, Any], bool]:
        """
        Get or generate content brief with smart caching
        
        Returns:
            Tuple of (brief_data, was_cached)
        """
        if not keyword.strip():
            return {"error": "Keyword is required"}, False
        
        # Check cache first unless forced refresh
        if not force_refresh:
            cached_data = cache_manager.get_smart_cached(
                data_type="brief",
                keyword=keyword,
                variant=variant,
                max_age_hours=24
            )
            
            if cached_data:
                # Update session state with cached data
                if "output" in cached_data:
                    st.session_state.brief_output = cached_data["output"]
                    st.session_state.brief_variant = cached_data.get("variant", variant)
                    st.session_state.brief_latency = cached_data.get("latency", 0)
                    st.session_state.brief_usage = cached_data.get("usage", {})
                
                return cached_data, True
        
        # Generate new brief
        try:
            output, prompt, latency, usage = generate_brief_with_variant(
                keyword=keyword, 
                variant=variant,
                plan_settings=st.session_state.get('plan_settings', {})
            )
            
            brief_data = {
                "output": output,
                "prompt": prompt,
                "latency": latency,
                "usage": usage,
                "variant": variant,
                "keyword": keyword,
                "generated_at": datetime.now().isoformat()
            }
            
            # Update session state
            st.session_state.brief_output = output
            st.session_state.brief_variant = variant
            st.session_state.brief_latency = latency
            st.session_state.brief_usage = usage
            
            # Cache the result
            cache_manager.set_smart_cached(
                data_type="brief",
                keyword=keyword,
                value=brief_data,
                variant=variant,
                expires_hours=24
            )
            
            return brief_data, False
            
        except Exception as e:
            error_data = {
                "error": f"Failed to generate brief: {str(e)}",
                "keyword": keyword,
                "variant": variant
            }
            return error_data, False
    
    @staticmethod
    def get_or_generate_serp(keyword: str, country: str = "US", language: str = "en", 
                           force_refresh: bool = False) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Get or generate SERP data with smart caching
        
        Returns:
            Tuple of (serp_data, was_cached)
        """
        if not keyword.strip():
            return None, False
        
        # Check cache first unless forced refresh
        if not force_refresh:
            cached_data = cache_manager.get_smart_cached(
                data_type="serp",
                keyword=keyword,
                country=country,
                language=language,
                max_age_hours=12  # SERP data changes more frequently
            )
            
            if cached_data:
                # Update session state with cached data
                st.session_state.serp_data = cached_data
                return cached_data, True
        
        # Generate new SERP data
        try:
            serp_data = fetch_serp_snapshot(
                keyword=keyword,
                country=country,
                language=language,
                plan_settings=st.session_state.get('plan_settings', {})
            )
            
            if serp_data:
                # Add metadata
                serp_data["keyword"] = keyword
                serp_data["country"] = country
                serp_data["language"] = language
                serp_data["generated_at"] = datetime.now().isoformat()
                
                # Update session state
                st.session_state.serp_data = serp_data
                
                # Cache the result
                cache_manager.set_smart_cached(
                    data_type="serp",
                    keyword=keyword,
                    value=serp_data,
                    country=country,
                    language=language,
                    expires_hours=12
                )
                
                return serp_data, False
            else:
                return None, False
                
        except Exception as e:
            print(f"Error generating SERP data: {e}")
            return None, False
    
    @staticmethod
    def get_or_generate_suggestions(keyword: str, force_refresh: bool = False) -> Tuple[Dict[str, str], bool]:
        """
        Get or generate AI suggestions with smart caching
        
        Returns:
            Tuple of (suggestions_data, was_cached)
        """
        if not keyword.strip():
            return {"error": "Keyword is required"}, False
        
        # Check cache first unless forced refresh
        if not force_refresh:
            cached_data = cache_manager.get_smart_cached(
                data_type="suggestions",
                keyword=keyword,
                max_age_hours=48  # Suggestions can be cached longer
            )
            
            if cached_data:
                # Update session state with cached data
                st.session_state.ai_suggestions = cached_data
                st.session_state.ai_suggestions_generated = True
                return cached_data, True
        
        # Generate new suggestions
        try:
            suggestions_data = SmartDataService._generate_ai_suggestions(keyword)
            
            # Add metadata
            suggestions_data["keyword"] = keyword
            suggestions_data["generated_at"] = datetime.now().isoformat()
            
            # Update session state
            st.session_state.ai_suggestions = suggestions_data
            st.session_state.ai_suggestions_generated = True
            
            # Cache the result
            cache_manager.set_smart_cached(
                data_type="suggestions",
                keyword=keyword,
                value=suggestions_data,
                expires_hours=48
            )
            
            return suggestions_data, False
            
        except Exception as e:
            error_data = {
                "error": f"Failed to generate suggestions: {str(e)}",
                "keyword": keyword
            }
            return error_data, False
    
    @staticmethod
    def _generate_ai_suggestions(keyword: str) -> Dict[str, str]:
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
    
    @staticmethod
    def check_data_freshness(keyword: str) -> Dict[str, Dict[str, Any]]:
        """Check the freshness of cached data for a keyword"""
        data_types = ["brief", "serp", "suggestions"]
        freshness_info = {}
        
        for data_type in data_types:
            cache_key = cache_manager.generate_smart_key(data_type, keyword)
            cached_data = cache_manager.get_smart_cached(data_type, keyword, max_age_hours=720)  # Very long age to check existence
            
            if cached_data:
                generated_at = cached_data.get("generated_at")
                if generated_at:
                    try:
                        gen_time = datetime.fromisoformat(generated_at)
                        age_hours = (datetime.now() - gen_time).total_seconds() / 3600
                        
                        freshness_info[data_type] = {
                            "exists": True,
                            "age_hours": round(age_hours, 1),
                            "is_fresh": age_hours < 24,  # Consider fresh if less than 24 hours
                            "generated_at": generated_at
                        }
                    except:
                        freshness_info[data_type] = {
                            "exists": True,
                            "age_hours": 0,
                            "is_fresh": True,
                            "generated_at": "unknown"
                        }
                else:
                    freshness_info[data_type] = {
                        "exists": True,
                        "age_hours": 0,
                        "is_fresh": True,
                        "generated_at": "unknown"
                    }
            else:
                freshness_info[data_type] = {
                    "exists": False,
                    "age_hours": None,
                    "is_fresh": False,
                    "generated_at": None
                }
        
        return freshness_info
    
    @staticmethod
    def invalidate_keyword_data(keyword: str):
        """Invalidate all cached data for a specific keyword"""
        cache_manager.invalidate_keyword_cache(keyword)
        
        # Also clear related session state
        if st.session_state.get("selected_keyword", "").lower() == keyword.lower():
            keys_to_clear = [
                "brief_output", "brief_variant", "brief_latency", "brief_usage",
                "serp_data", "ai_suggestions", "ai_suggestions_generated"
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
    
    @staticmethod
    def preload_keyword_data(keyword: str, include_serp: bool = True, include_suggestions: bool = True):
        """Preload all data for a keyword in the background"""
        results = {}
        
        # Always load brief (core requirement)
        brief_data, brief_cached = SmartDataService.get_or_generate_brief(keyword)
        results["brief"] = {"data": brief_data, "cached": brief_cached}
        
        # Load SERP if requested
        if include_serp:
            serp_data, serp_cached = SmartDataService.get_or_generate_serp(keyword)
            results["serp"] = {"data": serp_data, "cached": serp_cached}
        
        # Load suggestions if requested
        if include_suggestions:
            suggestions_data, suggestions_cached = SmartDataService.get_or_generate_suggestions(keyword)
            results["suggestions"] = {"data": suggestions_data, "cached": suggestions_cached}
        
        return results


# Convenience functions for backward compatibility
def get_or_generate_brief(keyword: str, variant: str = "A", force_refresh: bool = False) -> Tuple[Dict[str, Any], bool]:
    """Convenience function for brief generation"""
    return SmartDataService.get_or_generate_brief(keyword, variant, force_refresh)

def get_or_generate_serp(keyword: str, country: str = "US", language: str = "en", force_refresh: bool = False) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Convenience function for SERP generation"""
    return SmartDataService.get_or_generate_serp(keyword, country, language, force_refresh)

def get_or_generate_suggestions(keyword: str, force_refresh: bool = False) -> Tuple[Dict[str, str], bool]:
    """Convenience function for suggestions generation"""
    return SmartDataService.get_or_generate_suggestions(keyword, force_refresh)
