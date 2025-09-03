# api/core/gpt.py
import json


try:
    from openai import OpenAI  # type: ignore
except Exception:  # ImportError or version mismatch
    OpenAI = None  # type: ignore
from .env import get_openai_api_key

BRIEF_SYSTEM = (
    "You are an SEO content strategist. "
    "Given a target keyword, produce a concise content brief with sections: "
    "Target Reader, Search Intent, Angle, Outline (H2/H3), Key Entities, FAQs, "
    "and On-page checklist. Keep it practical and actionable."
)

def _get_client():
    if OpenAI is None:
        raise RuntimeError("OpenAI Python SDK v1+ is required. Run: pip install --upgrade openai")
    key = get_openai_api_key()
    if not key:
        # Keep error generic for now; routers can map to HTTP errors
        raise RuntimeError("Missing OPENAI_API_KEY in environment (.env)")
    return OpenAI(api_key=key)


def generate_brief(keyword: str, model: str) -> str:
    prompt = (
        f"Target keyword: {keyword}\n\n"
        "Create a content brief as described. "
        "Limit to ~500-700 words."
    )

    # Chat Completions (v1 SDK)
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.5,
        messages=[
            {"role": "system", "content": BRIEF_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()

def generate_suggestions(brief: str, serp: dict) -> list[str]:
    # Keep stub for now; we’ll wire this later after SERP integration.
    return [
        "(stub) Add comparison table of top results",
        "(stub) Include recent stats with citation",
        "(stub) Expand FAQs to address purchase objections",
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
