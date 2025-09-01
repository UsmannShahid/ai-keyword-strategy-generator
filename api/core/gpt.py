# api/core/gpt.py
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
