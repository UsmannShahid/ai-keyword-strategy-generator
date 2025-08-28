"""
High-level service functions for keyword generation.
Coordinates between LLM client and parsing logic.
"""

import json
import time
from typing import Dict, Any, Optional, Tuple, List, Union
from openai import OpenAI
import os

# Simple service functions for now - can be expanded later
def generate_writer_notes(
    *,
    keyword: str,
    brief_dict: Dict[str, Any],
    serp_summary: Optional[Dict[str, Any]] = None,
    variant: str = "A",
) -> Tuple[Dict[str, Any], bool, str, Optional[Dict[str, int]]]:
    """
    Generate structured Writer's Notes as JSON using prompt variants A/B.
    Returns: (notes_dict, is_json, prompt_used, usage_dict)
    """
    # Placeholder implementation
    prompt = f"Generate writer notes for keyword: {keyword}"
    notes = {"notes": f"Writer notes for {keyword}", "variant": variant}
    return notes, True, prompt, None

def generate_brief_with_variant(
    *,
    keyword: str,
    variant: str,
    plan_settings: dict = None,
) -> Tuple[str, str, float, Optional[Dict[str, int]]]:
    """
    Generate content brief with timing and usage tracking.
    
    Args:
        keyword: The keyword to generate content brief for
        variant: Prompt variant to use ('A' or 'B')
        plan_settings: Dictionary containing plan-specific settings including gpt_model
    
    Returns: 
        Tuple of (output_text, prompt_used, latency_ms, usage_dict)
    """
    t0 = time.monotonic()
    
    # Get OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        output = f"# Content Brief for '{keyword}'\n\n**Error**: OpenAI API key not configured."
        return output, "No API key", 0, None
    
    client = OpenAI(api_key=api_key)
    
    # Variant-specific prompts
    if variant == "A":
        prompt = f"""
        Create a comprehensive SEO content brief for the keyword: "{keyword}"
        
        Include:
        1. **Title Tag** (60 chars max, include target keyword)
        2. **Meta Description** (160 chars max)
        3. **Content Outline** (H1, H2, H3 structure)
        4. **Target Word Count**
        5. **Key Entities** to mention
        6. **Internal Link Opportunities**
        7. **FAQ Section** (3-5 questions)
        8. **Call-to-Action Ideas**
        
        Focus on search intent and user experience.
        """
    else:  # Variant B
        prompt = f"""
        Write a content brief for "{keyword}" that a freelance writer can easily follow.
        
        Format:
        ## Content Brief: {keyword}
        
        **Primary Goal**: [What should this content achieve?]
        **Target Audience**: [Who is this for?]
        **Tone**: [Professional/Casual/Expert]
        **Content Structure**:
        - Introduction (hook + preview)
        - Main sections (3-5 key topics)
        - Conclusion with clear next steps
        
        **SEO Requirements**:
        - Target keyword: "{keyword}"
        - Related keywords: [list 5-8 variations]
        - Meta title and description
        
        **Writer Notes**: [Any specific instructions or tips]
        """
    
    try:
        # Use plan-specific model or default to gpt-4o-mini
        model = plan_settings.get("gpt_model", "gpt-4o-mini") if plan_settings else "gpt-4o-mini"
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1500
        )
        
        output = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        } if response.usage else None
        
    except Exception as e:
        output = f"# Content Brief for '{keyword}'\n\n**Error generating content**: {str(e)}"
        usage = None
    
    latency_ms = (time.monotonic() - t0) * 1000
    return output, prompt, latency_ms, usage

def fetch_serp_snapshot(keyword: str, country: str = "US", language: str = "en", plan_settings: dict = None) -> list:
    """
    Return top results with keys: title, url, snippet.
    Uses different SERP providers based on user plan.
    """
    # SERP Provider Logic Based on Plan
    if plan_settings and plan_settings.get("serp_provider") == "searchapi":
        # Free users - use SearchAPI (cheaper option)
        serp_data = fetch_serp_with_searchapi(keyword, country, language, plan_settings)
    else:
        # Paid users - use SerpAPI (premium option)
        serp_data = fetch_serp_with_serpapi(keyword, country, language, plan_settings)
    
    return serp_data

def fetch_serp_with_searchapi(keyword: str, country: str = "US", language: str = "en", plan_settings: dict = None) -> list:
    """
    STUB: Fetch SERP data using SearchAPI (free tier provider).
    TODO: Implement actual SearchAPI integration
    """
    # Limit results for free users
    result_limit = plan_settings.get("serp_results_limit", 5) if plan_settings else 5
    
    base = keyword.lower()[:30] or "your topic"
    results = [
        {"title": f"{base} – community thread", "url": "https://reddit.com/r/example", "snippet": "User opinions and short answers."},
        {"title": f"Quick guide to {base}", "url": "https://example.com/quick-guide", "snippet": "A short guide updated in 2020."},
        {"title": f"{base} explained", "url": "https://example.org/what-is", "snippet": "Definition and basics."},
        {"title": f"Top 10 {base}", "url": "https://blog.example.com/top-10", "snippet": "Roundup with brief descriptions."},
        {"title": f"{base} buyer's checklist", "url": "https://shop.example.com/checklist", "snippet": "Key things to consider."},
        {"title": f"Best {base} 2024", "url": "https://reviews.example.com/best", "snippet": "Latest reviews and comparisons."},
        {"title": f"{base} vs alternatives", "url": "https://compare.example.com", "snippet": "Side-by-side comparison guide."},
    ]
    
    # Return limited results for free users
    return results[:result_limit]

def fetch_serp_with_serpapi(keyword: str, country: str = "US", language: str = "en", plan_settings: dict = None) -> list:
    """
    STUB: Fetch SERP data using SerpAPI (premium provider).
    TODO: Implement actual SerpAPI integration
    """
    # More results for paid users
    result_limit = plan_settings.get("serp_results_limit", 20) if plan_settings else 10
    
    base = keyword.lower()[:30] or "your topic"
    results = [
        {"title": f"{base} – community thread", "url": "https://reddit.com/r/example", "snippet": "User opinions and short answers."},
        {"title": f"Quick guide to {base}", "url": "https://example.com/quick-guide", "snippet": "A short guide updated in 2020."},
        {"title": f"{base} explained", "url": "https://example.org/what-is", "snippet": "Definition and basics."},
        {"title": f"Top 10 {base}", "url": "https://blog.example.com/top-10", "snippet": "Roundup with brief descriptions."},
        {"title": f"{base} buyer's checklist", "url": "https://shop.example.com/checklist", "snippet": "Key things to consider."},
        {"title": f"Best {base} 2024", "url": "https://reviews.example.com/best", "snippet": "Latest reviews and comparisons."},
        {"title": f"{base} vs alternatives", "url": "https://compare.example.com", "snippet": "Side-by-side comparison guide."},
        {"title": f"How to choose {base}", "url": "https://guides.example.com/choose", "snippet": "Expert buying guide with criteria."},
        {"title": f"{base} reviews and ratings", "url": "https://ratings.example.com", "snippet": "User reviews and star ratings."},
        {"title": f"Professional {base} setup", "url": "https://pro.example.com/setup", "snippet": "Advanced configuration guide."},
        {"title": f"{base} troubleshooting", "url": "https://support.example.com", "snippet": "Common issues and solutions."},
        {"title": f"Latest {base} trends", "url": "https://trends.example.com", "snippet": "Industry trends and innovations."},
        {"title": f"{base} case studies", "url": "https://business.example.com", "snippet": "Real-world implementation examples."},
        {"title": f"Advanced {base} techniques", "url": "https://advanced.example.com", "snippet": "Expert-level strategies and tips."},
        {"title": f"{base} cost analysis", "url": "https://costs.example.com", "snippet": "Pricing breakdown and ROI analysis."},
        {"title": f"Enterprise {base} solutions", "url": "https://enterprise.example.com", "snippet": "Large-scale implementation guide."},
        {"title": f"{base} security considerations", "url": "https://security.example.com", "snippet": "Best practices for secure setup."},
        {"title": f"Future of {base}", "url": "https://future.example.com", "snippet": "Emerging trends and predictions."},
        {"title": f"{base} integration guide", "url": "https://integrations.example.com", "snippet": "How to integrate with other tools."},
        {"title": f"{base} performance optimization", "url": "https://optimize.example.com", "snippet": "Tips for maximum efficiency."},
    ]
    
    # Return more results for paid users
    return results[:result_limit]

class KeywordService:
    """Service class for keyword generation operations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def generate_keywords(
        self, 
        business_desc: str, 
        industry: str = "", 
        audience: str = "", 
        country: str = "US",
        location: str = "",
        prompt_template: str = "default_seo",
        plan_settings: dict = None
    ) -> Dict[str, Any]:
        """Generate keywords for a business with quick-win scores."""
        if not self.client:
            # Fallback with realistic mock data
            return {
                "informational": [
                    {"keyword": f"how to choose {business_desc}", "volume": 850, "difficulty": 45, "quick_win_score": 72},
                    {"keyword": f"{business_desc} guide for beginners", "volume": 620, "difficulty": 38, "quick_win_score": 78},
                    {"keyword": f"what is {business_desc}", "volume": 1200, "difficulty": 55, "quick_win_score": 65}
                ],
                "transactional": [
                    {"keyword": f"buy {business_desc} online", "volume": 940, "difficulty": 42, "quick_win_score": 75},
                    {"keyword": f"best {business_desc} deals", "volume": 720, "difficulty": 35, "quick_win_score": 82},
                    {"keyword": f"affordable {business_desc}", "volume": 580, "difficulty": 30, "quick_win_score": 85}
                ],
                "branded": [
                    {"keyword": f"{business_desc} reviews 2024", "volume": 450, "difficulty": 28, "quick_win_score": 88},
                    {"keyword": f"{business_desc} vs competitors", "volume": 380, "difficulty": 40, "quick_win_score": 76}
                ]
            }
        
        try:
            # Country-specific context
            country_context = {
                "US": "United States market",
                "CA": "Canadian market", 
                "GB": "UK market",
                "AU": "Australian market",
                "DE": "German market",
                "FR": "French market",
                "ES": "Spanish market",
                "IT": "Italian market",
                "NL": "Dutch market",
                "BR": "Brazilian market",
                "MX": "Mexican market",
                "JP": "Japanese market",
                "IN": "Indian market",
                "SG": "Singapore market"
            }.get(country, f"{country} market")
            
            # Real API call with structured prompt
            prompt = f"""
            Generate 8-12 SEO keywords for this business: {business_desc}
            Industry: {industry or 'general'}
            Audience: {audience or 'general consumers'}
            Target Market: {country_context}
            Location: {location or 'global'}
            
            Consider regional search patterns, local terminology, and market-specific needs for {country_context}.
            
            Return a JSON object with this exact structure:
            {{
                "informational": [
                    {{"keyword": "how to use [product]", "volume": 850, "difficulty": 45, "quick_win_score": 72}}
                ],
                "transactional": [
                    {{"keyword": "buy [product] online", "volume": 940, "difficulty": 42, "quick_win_score": 75}}
                ],
                "branded": [
                    {{"keyword": "[brand] reviews", "volume": 450, "difficulty": 28, "quick_win_score": 88}}
                ]
            }}
            
            Quick-win score = (volume/10) + (100-difficulty). Higher is better.
            """
            
            # Use plan-specific model or default to gpt-4o-mini
            model = plan_settings.get("gpt_model", "gpt-4o-mini") if plan_settings else "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"API error: {e}")
            # Fallback to mock data
            return self.generate_keywords(business_desc, industry, audience, location, prompt_template)


# ============================================================================
# KEYWORD ANALYSIS STUBS (Plan-Based Features)
# ============================================================================

def build_keyword_analysis_prompt(keywords: List[Dict[str, Any]]) -> str:
    """
    Build a comprehensive prompt for GPT keyword analysis and clustering.
    
    Args:
        keywords: List of keyword dictionaries with volume, competition, CPC data
        
    Returns:
        Formatted prompt string for GPT analysis
    """
    if not keywords:
        return "No keywords provided for analysis."
    
    # Format keywords with metrics
    keyword_list = "\n".join([
        f"- {kw.get('Keyword', kw.get('keyword', 'Unknown'))} "
        f"(Volume: {kw.get('Search Volume', kw.get('volume', 0)):,}, "
        f"CPC: ${kw.get('CPC', kw.get('cpc', 0)):.2f}, "
        f"Competition: {kw.get('Competition', kw.get('competition', 0)):.0%})"
        for kw in keywords
    ])
    
    prompt = f"""You are an expert SEO strategist analyzing keywords for content marketing and search optimization.

Given the following keyword list with search volume, cost-per-click (CPC), and competition data, perform a comprehensive analysis:

### KEYWORD DATA:
{keyword_list}

### ANALYSIS REQUIREMENTS:

1. **INTENT CLASSIFICATION** - Group keywords by search intent:
   - **Informational**: How-to, guides, explanations (users seeking knowledge)
   - **Commercial**: Reviews, comparisons, "best" keywords (research phase)
   - **Transactional**: "Buy", "price", specific products (ready to purchase)
   - **Navigational**: Brand names, specific sites (looking for specific destination)

2. **QUICK WIN IDENTIFICATION** - Find 3-5 keywords that are:
   - Low to medium competition (< 50% competition score)
   - Decent search volume (> 1,000 monthly searches)
   - Reasonable CPC (indicates commercial value)
   - High potential ROI for content creation

3. **COMPETITIVE ANALYSIS** - Assess:
   - Overall competition landscape
   - Opportunities for content gaps
   - Difficulty vs opportunity matrix

4. **STRATEGIC RECOMMENDATIONS** - Provide:
   - Priority order for content creation
   - Content types that would perform well
   - Long-tail opportunities
   - Seasonal considerations if applicable

### OUTPUT FORMAT:
Use clear markdown formatting with sections for each analysis type. Include specific keyword recommendations with reasoning.

### ANALYSIS:"""

    return prompt


def analyze_keywords_with_gpt(keywords_data: Union[List[Dict[str, Any]], Dict[str, Any]], plan_settings: dict = None) -> Dict[str, Any]:
    """
    Advanced keyword analysis using GPT for clustering, intent analysis, and Quick Win identification.
    
    Args:
        keywords_data: Keyword data (list of dicts or categorized dict)
        plan_settings: User plan settings
    
    Returns:
        Analysis data including GPT insights, quick wins, and recommendations
    """
    if not plan_settings or not plan_settings.get("keyword_analysis_enabled", False):
        return {"error": "Keyword analysis not available for your plan"}
    
    # Convert keywords_data to list format if needed
    keywords_list = []
    if isinstance(keywords_data, dict):
        # Handle categorized keywords from AI generation
        for category, kws in keywords_data.items():
            for kw in kws:
                if isinstance(kw, dict):
                    keywords_list.append(kw)
                else:
                    # Convert string to dict format
                    keywords_list.append({
                        "Keyword": str(kw),
                        "Search Volume": 1000,  # Default values
                        "Competition": 0.5,
                        "CPC": 1.0,
                        "category": category
                    })
    else:
        keywords_list = keywords_data
    
    if not keywords_list:
        return {"error": "No keywords provided for analysis"}
    
    try:
        # Use plan-specific model
        model = plan_settings.get("gpt_model", "gpt-4o-mini")
        
        # Build analysis prompt
        prompt = build_keyword_analysis_prompt(keywords_list)
        
        # Get OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OpenAI API key not configured"}
        
        client = OpenAI(api_key=api_key)
        
        # Make GPT API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert SEO strategist specializing in keyword research and content strategy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        gpt_analysis = response.choices[0].message.content
        
        # Parse and structure the response
        analysis_result = {
            "raw_analysis": gpt_analysis,
            "model_used": model,
            "analysis_timestamp": time.time(),
            "keywords_analyzed": len(keywords_list),
            "total_search_volume": sum(kw.get('Search Volume', kw.get('volume', 0)) for kw in keywords_list),
            "avg_competition": sum(kw.get('Competition', kw.get('competition', 0)) for kw in keywords_list) / len(keywords_list) if keywords_list else 0,
            "avg_cpc": sum(kw.get('CPC', kw.get('cpc', 0)) for kw in keywords_list) / len(keywords_list) if keywords_list else 0
        }
        
        return analysis_result
        
    except Exception as e:
        print(f"Error in GPT keyword analysis: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}


def analyze_keywords_with_gpt_old(keywords_data: Dict[str, Any], plan_settings: dict = None) -> Dict[str, Any]:
    """
    STUB: Advanced keyword analysis using GPT (paid users only).
    TODO: Implement actual AI-powered keyword analysis
    
    Args:
        keywords_data: Generated keywords from KeywordService
        plan_settings: User plan settings
    
    Returns:
        Analysis data including insights, opportunities, and recommendations
    """
    if not plan_settings or not plan_settings.get("keyword_analysis_enabled", False):
        return {"error": "Keyword analysis not available for your plan"}
    
    # Use plan-specific model
    model = plan_settings.get("gpt_model", "gpt-4o-mini")
    
    # STUB: Mock analysis for now
    analysis = {
        "insights": {
            "total_keywords": sum(len(keywords_data.get(cat, [])) for cat in keywords_data.keys()),
            "avg_difficulty": 45.2,
            "high_opportunity_count": 8,
            "competition_level": "Medium"
        },
        "opportunities": [
            {"keyword": "best ergonomic office chair", "reason": "Low competition + high intent", "priority": "High"},
            {"keyword": "affordable standing desk", "reason": "Rising trend + good volume", "priority": "Medium"},
            {"keyword": "home office setup guide", "reason": "Informational gap identified", "priority": "Medium"}
        ],
        "recommendations": [
            "Focus on long-tail keywords with buyer intent",
            "Consider seasonal trends for office furniture",
            "Target 'work from home' related modifiers"
        ],
        "model_used": model,
        "analysis_timestamp": time.time()
    }
    
    return analysis


def extract_quick_win_keywords(gpt_response: str) -> List[str]:
    """
    Extract Quick Win keywords from GPT analysis response.
    
    Args:
        gpt_response: Raw GPT analysis text
        
    Returns:
        List of extracted Quick Win keywords
    """
    import re
    
    # Look for Quick Win sections with numbered lists
    quick_win_patterns = [
        r"### 🔥 Quick Win Keywords?:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"Quick Win Keywords?:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"🔥.*Quick Win.*:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"### Quick Wins?:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"## Quick Win.*:?\s*\n((?:\d+\.\s.+\n?)+)"
    ]
    
    quick_wins = []
    
    for pattern in quick_win_patterns:
        matches = re.search(pattern, gpt_response, re.MULTILINE | re.IGNORECASE)
        if matches:
            lines = matches.group(1).strip().split('\n')
            for line in lines:
                # Extract keyword from numbered list
                keyword_match = re.match(r'\d+\.\s*(.+)', line.strip())
                if keyword_match:
                    keyword = keyword_match.group(1).strip()
                    # Clean up any extra formatting
                    keyword = re.sub(r'\*\*|\*|`', '', keyword)
                    if keyword and len(keyword) > 3:  # Basic validation
                        quick_wins.append(keyword)
    
    # Fallback: look for any keywords in bullet points or lists
    if not quick_wins:
        bullet_patterns = [
            r"[-*]\s*([^-*\n]+?)(?:\s*\(|$)",
            r"•\s*([^•\n]+?)(?:\s*\(|$)"
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, gpt_response)
            for match in matches:
                keyword = match.strip()
                keyword = re.sub(r'\*\*|\*|`', '', keyword)
                if keyword and len(keyword) > 3 and len(keyword) < 80:
                    quick_wins.append(keyword)
    
    # Remove duplicates and limit results
    return list(dict.fromkeys(quick_wins))[:5]


def generate_suggestions(brief: str, serp_data: List[Dict], plan_settings: dict = None) -> List[str]:
    """
    Generate AI-powered content suggestions based on brief and SERP data.
    
    Args:
        brief: Generated content brief
        serp_data: SERP analysis data
        plan_settings: User plan settings
        
    Returns:
        List of content suggestions
    """
    try:
        # Use plan-specific model
        model = plan_settings.get("gpt_model", "gpt-4o-mini") if plan_settings else "gpt-4o-mini"
        
        # Prepare SERP context
        serp_titles = []
        serp_snippets = []
        if serp_data:
            for result in serp_data[:5]:  # Top 5 results
                if isinstance(result, dict):
                    serp_titles.append(result.get('title', ''))
                    serp_snippets.append(result.get('snippet', ''))
        
        serp_context = f"""
TOP SERP TITLES:
{chr(10).join(f"- {title}" for title in serp_titles[:5])}

TOP SERP SNIPPETS:
{chr(10).join(f"- {snippet[:100]}..." for snippet in serp_snippets[:3])}
"""
        
        prompt = f"""Based on this content brief and SERP analysis, provide 5 specific, actionable content suggestions.

CONTENT BRIEF:
{brief[:1000]}

{serp_context}

Generate 5 specific suggestions for creating better content than competitors:

1. Content gaps to fill
2. Unique angles to explore  
3. Better formatting/structure ideas
4. Additional topics to cover
5. Engagement improvements

Keep each suggestion under 50 words and actionable."""

        # Get OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ["OpenAI API key not configured"]
        
        client = OpenAI(api_key=api_key)
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert content strategist specializing in competitive content analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        suggestions_text = response.choices[0].message.content
        
        # Parse suggestions from numbered list
        import re
        suggestions = []
        lines = suggestions_text.split('\n')
        for line in lines:
            match = re.match(r'\d+\.\s*(.+)', line.strip())
            if match:
                suggestions.append(match.group(1).strip())
        
        return suggestions[:5] if suggestions else ["Analysis complete - ready for content creation"]
        
    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")
        return [f"Unable to generate suggestions: {str(e)}"]


def show_analysis(ai_analysis: Dict[str, Any]) -> None:
    """
    Display AI keyword analysis in the UI with enhanced GPT-powered insights.
    
    Args:
        ai_analysis: Analysis data from analyze_keywords_with_gpt
    """
    import streamlit as st
    
    if "error" in ai_analysis:
        st.warning(f"⚠️ {ai_analysis['error']}")
        st.info("💎 Upgrade to Premium for advanced keyword analysis!")
        return
    
    st.markdown("### � AI Keyword Clustering + Quick Wins")
    
    # Check if we have new GPT analysis format
    if "raw_analysis" in ai_analysis:
        # Display summary metrics first
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Keywords Analyzed", ai_analysis.get("keywords_analyzed", 0))
        with col2:
            total_volume = ai_analysis.get("total_search_volume", 0)
            st.metric("Total Volume", f"{total_volume:,}")
        with col3:
            avg_comp = ai_analysis.get("avg_competition", 0)
            st.metric("Avg Competition", f"{avg_comp:.0%}")
        with col4:
            avg_cpc = ai_analysis.get("avg_cpc", 0)
            st.metric("Avg CPC", f"${avg_cpc:.2f}")
        
        st.divider()
        
        # Display the full GPT analysis
        st.markdown("#### 📊 Detailed Analysis")
        st.markdown(ai_analysis["raw_analysis"])
        
        # Extract and display Quick Win keywords as buttons
        quick_wins = extract_quick_win_keywords(ai_analysis["raw_analysis"])
        if quick_wins:
            st.divider()
            st.markdown("### 🚀 Generate Brief from Quick Win")
            st.markdown("Click any Quick Win keyword to generate a complete content brief with SERP analysis:")
            
            cols = st.columns(min(len(quick_wins), 3))
            for i, keyword in enumerate(quick_wins):
                with cols[i % 3]:
                    if st.button(f"📝 {keyword}", key=f"quick_win_{i}", help=f"Generate brief for '{keyword}'"):
                        st.session_state.selected_keyword = keyword
                        st.session_state.selected_keyword_source = "Quick Win"
                        st.session_state.quick_win_active = True
                        st.rerun()
        
        # Model and timestamp info
        st.caption(f"Analysis powered by {ai_analysis.get('model_used', 'AI')} • "
                  f"Generated {time.strftime('%H:%M:%S', time.localtime(ai_analysis.get('analysis_timestamp', time.time())))}")
    
    else:
        # Fallback to old format for compatibility
        # Insights section (old format)
        insights = ai_analysis.get("insights", {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Keywords", insights.get("total_keywords", 0))
        with col2:
            st.metric("Avg Difficulty", f"{insights.get('avg_difficulty', 0)}/100")
        with col3:
            st.metric("High Opportunities", insights.get("high_opportunity_count", 0))
        with col4:
            st.metric("Competition", insights.get("competition_level", "Unknown"))
        
        # Opportunities section
        st.markdown("#### 🎯 Top Opportunities")
        opportunities = ai_analysis.get("opportunities", [])
        for opp in opportunities:
            priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(opp.get("priority", "Low"), "⚪")
            st.markdown(f"{priority_color} **{opp.get('keyword', '')}** - {opp.get('reason', '')}")
        
        # Recommendations section
        st.markdown("#### 💡 AI Recommendations")
        recommendations = ai_analysis.get("recommendations", [])
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
        
        # Model info
        st.caption(f"Analysis powered by {ai_analysis.get('model_used', 'AI')}")

def check_keyword_analysis_availability(plan_settings: dict = None) -> bool:
    """
    STUB: Check if keyword analysis is available for current plan.
    
    Args:
        plan_settings: User plan settings
        
    Returns:
        True if analysis is available, False otherwise
    """
    if not plan_settings:
        return False
    
    return plan_settings.get("keyword_analysis_enabled", False)