# api/core/gpt.py
import json


try:
    from openai import OpenAI  # type: ignore
except Exception:  # ImportError or version mismatch
    OpenAI = None  # type: ignore
from .env import get_openai_api_key

BRIEF_SYSTEM = (
    "You're a content strategist who helps regular people create amazing content. Your job is to write "
    "content briefs that sound natural and helpful - not robotic or overly formal. Think like you're "
    "advising a friend who wants to write great content about their topic. "
    "Use conversational language, practical examples, and avoid SEO jargon. "
    "Return JSON with these keys: target_reader, search_intent, angle, outline, key_entities, faqs, "
    "checklist, meta_title, meta_description. Outline should be objects with 'heading' and 'description'."
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
        # Variant B - Alternative creative approach
        system_msg = (
            "You're a creative content strategist who loves finding fresh, unique angles. Help someone "
            "create content that stands out from the crowd - think outside the box while staying practical. "
            "Write like you're brainstorming with a creative friend. Use natural, conversational language "
            "and avoid corporate buzzwords. Focus on what would genuinely interest readers. "
            "Return JSON with these keys: target_reader, search_intent, angle, outline, key_entities, faqs, "
            "checklist, meta_title, meta_description. Outline should be objects with 'heading' and 'description'."
        )
        user_prompt = (
            f"Let's create something different about '{keyword}' - what's a fresh angle nobody else is taking?\n\n"
            "Think about:\n"
            "• target_reader: Who would really benefit from this? (be specific about their situation)\n"
            "• search_intent: What are they actually hoping to find?\n"
            "• angle: What's your unique spin that makes this interesting?\n"
            "• outline: Break it down into sections that flow naturally (heading + description for each)\n"
            "• key_entities: What terms/brands/concepts should we mention?\n"
            "• faqs: What questions do real people ask about this?\n"
            "• checklist: Practical steps to make the content great\n"
            "• meta_title: A compelling title under 60 characters\n"
            "• meta_description: Hook readers in under 160 characters"
        )
    else:
        # Variant A - Standard comprehensive approach
        system_msg = BRIEF_SYSTEM
        user_prompt = (
            f"I need help creating great content about '{keyword}'. Can you help me put together a solid plan?\n\n"
            "Here's what would be helpful:\n"
            "• target_reader: Who's this content really for? (think about their specific needs)\n"
            "• search_intent: What are they trying to accomplish when they search for this?\n"
            "• angle: What's your recommended approach to make this valuable?\n"
            "• outline: How should I structure this? (section headings with brief descriptions)\n"
            "• key_entities: What important terms, brands, or concepts should I include?\n"
            "• faqs: What questions do people commonly have about this topic?\n"
            "• checklist: What are the key things I should remember while writing?\n"
            "• meta_title: A good title for search results (under 60 characters)\n"
            "• meta_description: A description that gets people to click (under 160 characters)\n\n"
            "Make it practical and easy to follow - I want to create something that actually helps people!"
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
        # Fallback to natural, helpful format
        return {
            "target_reader": f"People who are exploring {keyword} and want practical, easy-to-understand guidance",
            "search_intent": "Looking for helpful information and actionable advice",
            "angle": f"A practical, no-nonsense guide that actually helps people understand {keyword}",
            "outline": [
                {"heading": "Getting Started", "description": f"What you need to know about {keyword} before diving in"},
                {"heading": "Why This Matters", "description": f"Real benefits and reasons people care about {keyword}"},
                {"heading": "Your Options", "description": f"Different approaches and what works best for different situations"},
                {"heading": "Making the Right Choice", "description": f"How to decide what's best for your specific needs"},
                {"heading": "Next Steps", "description": f"What to do after you've learned about {keyword}"}
            ],
            "key_entities": [keyword.title()],
            "faqs": [{"question": f"What exactly is {keyword}?", "answer": "We'll explain this clearly with examples that make sense."}],
            "checklist": ["Write naturally - don't stuff keywords", "Add helpful images that support your points", "Link to other useful resources", "Make sure your intro hooks readers", "Break up text with clear headings"],
            "meta_title": f"{keyword.title()}: A Practical Guide That Actually Helps",
            "meta_description": f"Get clear, practical advice about {keyword}. No jargon, no fluff - just the info you actually need."
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

