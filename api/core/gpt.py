# api/core/gpt.py
import json


try:
    from openai import OpenAI  # type: ignore
except Exception:  # ImportError or version mismatch
    OpenAI = None  # type: ignore
from .env import get_openai_api_key

BRIEF_SYSTEM = (
    "You are an SEO content strategist. Generate a structured content brief in JSON format. "
    "Output STRICT JSON with these exact keys: target_reader, search_intent, angle, "
    "outline, key_entities, faqs, checklist. Make it practical and actionable for non-SEO experts."
)


def _get_client():
    if OpenAI is None:
        raise RuntimeError("OpenAI Python SDK v1+ is required. Run: pip install --upgrade openai")
    key = get_openai_api_key()
    if not key:
        # Keep error generic for now; routers can map to HTTP errors
        raise RuntimeError("Missing OPENAI_API_KEY in environment (.env)")
    return OpenAI(api_key=key)


def generate_brief(keyword: str, model: str, variant: str = "a") -> dict:
    if variant.lower() == "b":
        # Variant B - Alternative approach with different angle
        system_msg = (
            "You are an SEO content strategist specializing in creative, alternative approaches. "
            "Generate a structured content brief in JSON format with these exact keys: "
            "target_reader, search_intent, angle, outline, key_entities, faqs, checklist. "
            "Focus on unique angles and unexplored approaches. Make it actionable for non-SEO experts."
        )
        user_prompt = (
            f"Target keyword: {keyword}\n\n"
            "Create an ALTERNATIVE content brief with a fresh, creative angle that stands out. "
            "JSON format with: target_reader (who this content is for), search_intent (what users want), "
            "angle (your unique approach), outline (array of H2/H3 sections), key_entities (important terms/brands), "
            "faqs (array of Q&A), checklist (array of on-page optimization steps)."
        )
    else:
        # Variant A - Standard comprehensive approach
        system_msg = BRIEF_SYSTEM
        user_prompt = (
            f"Target keyword: {keyword}\n\n"
            "Create a comprehensive content brief. Return JSON with: "
            "target_reader (who this content is for), search_intent (what users want), "
            "angle (your content approach), outline (array of H2/H3 sections), "
            "key_entities (important terms/brands), faqs (array of Q&A), "
            "checklist (array of on-page optimization steps)."
        )

    # Chat Completions (v1 SDK)
    client = _get_client()
    
    # Check if model supports JSON mode
    json_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-1106"]
    supports_json = any(json_model in model for json_model in json_models)
    
    if supports_json:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.7 if variant.lower() == "b" else 0.5,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"}
        )
    else:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.7 if variant.lower() == "b" else 0.5,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ]
        )
    
    try:
        return json.loads(resp.choices[0].message.content.strip())
    except json.JSONDecodeError:
        # Fallback to plain text format
        return {
            "target_reader": "General audience interested in " + keyword,
            "search_intent": "Informational and commercial research",
            "angle": "Comprehensive guide covering all aspects",
            "outline": ["Introduction", "Main Benefits", "How to Choose", "Comparison", "Conclusion"],
            "key_entities": [keyword],
            "faqs": [{"q": f"What is {keyword}?", "a": "A detailed explanation..."}],
            "checklist": ["Include target keyword in title", "Add relevant images", "Include internal links"]
        }


def analyze_serp_data(keyword: str, serp_results: list, model: str) -> dict:
    """Analyze SERP results to provide competitive insights."""
    if not serp_results:
        return {
            "difficulty": "Unknown",
            "content_gaps": ["No SERP data available"],
            "competitor_insights": [],
            "opportunities": ["Analyze competitor content when SERP data is available"]
        }
    
    # Prepare SERP data for analysis
    top_results = []
    for i, result in enumerate(serp_results[:5]):  # Analyze top 5
        top_results.append({
            "position": i + 1,
            "title": result.get("title", ""),
            "snippet": result.get("snippet", ""),
            "url": result.get("url", "")
        })
    
    system_msg = (
        "You are an SEO competitive analyst. Analyze the top search results for a keyword and provide "
        "actionable insights in JSON format with keys: difficulty, content_gaps, competitor_insights, opportunities. "
        "Make recommendations practical for non-SEO experts."
    )
    
    user_prompt = f"""
Keyword: {keyword}
Top search results: {json.dumps(top_results)}

Analyze these search results and return JSON with:
- difficulty: "Low/Medium/High" ranking difficulty based on result types
- content_gaps: Array of content opportunities not covered by top results  
- competitor_insights: Array of key observations about top-ranking pages
- opportunities: Array of specific actionable recommendations

Focus on practical advice for someone creating content around this keyword.
"""

    client = _get_client()
    
    # Check if model supports JSON mode
    json_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-1106"]
    supports_json = any(json_model in model for json_model in json_models)
    
    try:
        if supports_json:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"}
            )
        else:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ]
            )
        
        return json.loads(resp.choices[0].message.content.strip())
    except (json.JSONDecodeError, Exception):
        # Fallback analysis
        return {
            "difficulty": "Medium",
            "content_gaps": ["Consider unique angles not covered by competitors"],
            "competitor_insights": [f"Found {len(top_results)} competing pages for {keyword}"],
            "opportunities": ["Create comprehensive content covering gaps in top results"]
        }


def generate_comprehensive_strategy(keyword: str, brief: dict, serp_results: list, serp_analysis: dict, model: str) -> dict:
    """Generate a comprehensive SEO strategy based on content brief and SERP analysis."""
    
    # Prepare data for strategy generation
    strategy_input = {
        "keyword": keyword,
        "brief_summary": {
            "target_reader": brief.get("target_reader", ""),
            "search_intent": brief.get("search_intent", ""),
            "angle": brief.get("angle", ""),
            "outline_count": len(brief.get("outline", [])),
        },
        "competition": {
            "difficulty": serp_analysis.get("difficulty", "Unknown") if serp_analysis else "Unknown",
            "top_competitors": len(serp_results),
            "content_gaps": serp_analysis.get("content_gaps", []) if serp_analysis else [],
        }
    }
    
    system_msg = (
        "You are a comprehensive SEO strategist. Create a detailed, actionable SEO strategy "
        "in JSON format with keys: content_strategy, technical_seo, link_building, measurement. "
        "Make all recommendations practical and specific for non-SEO experts."
    )
    
    user_prompt = f"""
Create a comprehensive SEO strategy for this scenario:

Keyword: {keyword}
Target Content: {strategy_input["brief_summary"]}
Competition Level: {strategy_input["competition"]["difficulty"]}
Identified Content Gaps: {strategy_input["competition"]["content_gaps"]}

Return JSON with these sections:
- content_strategy: Array of specific content creation and optimization tactics
- technical_seo: Array of technical improvements needed
- link_building: Array of link acquisition strategies 
- measurement: Array of KPIs and tracking methods

Focus on actionable, step-by-step guidance that a business owner can implement.
"""

    client = _get_client()
    
    # Check if model supports JSON mode
    json_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-1106"]
    supports_json = any(json_model in model for json_model in json_models)
    
    try:
        if supports_json:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"}
            )
        else:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt},
                ]
            )
        
        return json.loads(resp.choices[0].message.content.strip())
    except (json.JSONDecodeError, Exception):
        # Fallback strategy
        return {
            "content_strategy": [
                f"Create comprehensive content targeting '{keyword}' with focus on user intent",
                "Include comparison sections to address purchase decisions",
                "Add FAQ section covering common user questions",
                "Optimize content length to match top competitors"
            ],
            "technical_seo": [
                "Ensure fast page loading speed (under 3 seconds)",
                "Optimize for mobile responsiveness",
                "Add structured data markup",
                "Implement proper heading hierarchy (H1, H2, H3)"
            ],
            "link_building": [
                "Reach out to industry publications for guest posting",
                "Create shareable infographics and tools",
                "Build relationships with complementary businesses",
                "Submit to relevant industry directories"
            ],
            "measurement": [
                f"Track keyword rankings for '{keyword}' and related terms",
                "Monitor organic traffic growth month-over-month",
                "Measure conversion rate from organic traffic",
                "Track backlink acquisition and domain authority"
            ]
        }


def generate_suggestions(brief: str, serp: dict) -> list[str]:
    # Legacy function - kept for backward compatibility
    return [
        "Create comprehensive content covering all user questions",
        "Include comparison sections and user testimonials",
        "Optimize for featured snippets with structured data",
        "Build topic clusters around related keywords"
    ]


def generate_product_description(
    product_name: str,
    features: list[str],
    channel: str,
    tone: str,
    length: str,
    model: str
) -> dict:
    system_msg = (
        "You are an expert ecommerce copywriter. "
        "Write conversion-optimized product copy for the specified platform. "
        "Always return JSON with: title, bullets, description, seo_keywords."
    )

    user_prompt = f"""
Product: {product_name}
Features: {features}
Channel: {channel}
Tone: {tone}
Length: {length}

Rules:
- Title: optimized for {channel}, max 200 characters
- Bullets: 4-6 concise benefit-driven bullet points
- Description: persuasive, structured (50-150 words for medium)
- SEO keywords: 5-8 related terms
Output STRICT JSON.
"""
    client = _get_client()
    
    # Check if model supports JSON mode
    json_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-1106"]
    supports_json = any(json_model in model for json_model in json_models)
    
    if supports_json:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.6,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"}
        )
    else:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.6,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ]
        )

    txt = resp.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except Exception:
        return {
            "title": product_name,
            "bullets": features,
            "description": "Could not generate product description.",
            "seo_keywords": [],
        }

