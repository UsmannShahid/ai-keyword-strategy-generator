# api/core/keywords.py
import pandas as pd
from pathlib import Path
import json
from typing import List, Dict, Optional
from api.core.config import get_settings
from api.core.gpt import _get_client  # reuse your OpenAI client

GKP_PATH = Path("data/gkp_keywords.csv")


def load_gkp_keywords(topic: str, max_results: int = 20, industry: str = None, audience: str = None):
    """Generate keyword suggestions using AI for any topic."""
    try:
        # Use AI to generate relevant keywords
        result = generate_keywords_with_ai(topic, max_results, industry, audience)
        if result:
            return result
    except Exception as e:
        pass  # Fall through to CSV fallback
        
    # Fallback to CSV if AI fails or returns empty
    csv_result = load_keywords_from_csv(topic, max_results)
    if csv_result:
        return csv_result
        
    # Final fallback - always generate something
    return generate_basic_keywords_fallback(topic, max_results)


def generate_keywords_with_ai(topic: str, max_results: int = 20, industry: str = None, audience: str = None):
    """Generate keyword suggestions using OpenAI GPT with focus on winnability."""
    client = _get_client()
    
    # Add context if provided
    context_note = ""
    if industry or audience:
        context_parts = []
        if industry:
            context_parts.append(f"Industry: {industry}")
        if audience:
            context_parts.append(f"Target audience: {audience}")
        context_note = f"\n\nCONTEXT: {' | '.join(context_parts)}\nConsider this context when generating keywords."
    
    # Generate more keywords server-side for better Quick Wins pool
    server_pool_size = min(max_results * 5, 100)  # 5x more for candidate pool
    prompt = f"""Generate {server_pool_size} WINNABLE keyword suggestions related to "{topic}".{context_note}
    
FOCUS ON WINNABLE KEYWORDS:
- 70% should have competition 0.1-0.4 (low to medium-low)
- 20% should have competition 0.4-0.6 (medium)  
- 10% can have competition 0.6+ (high)
- Prioritize long-tail keywords (3-6 words)
- Include location-based modifiers ("near me", city names)
- Mix informational and commercial intent
- Target realistic search volumes (100-10,000)

For each keyword, provide:
- keyword: the actual search term (prefer 3-6 words)
- volume: realistic monthly search volume (100-10,000 range)
- cpc: estimated cost per click in USD (0.2-3.0 range)
- competition: competition level (weighted toward 0.1-0.4 for winnability)

Keyword types to generate:
- Long-tail variations: "{topic} for [specific use case]"
- Question-based: "how to choose {topic}", "what is the best {topic}"
- Location-based: "{topic} near me", "local {topic} store"
- Problem-solving: "{topic} for [problem]", "{topic} reviews"
- Comparison: "{topic} vs", "best {topic} for"
- Commercial: "buy {topic}", "cheap {topic}", "{topic} deals"

Return ONLY valid JSON in this format:
{{"keywords": [{{"keyword": "example keyword", "volume": 1500, "cpc": 1.25, "competition": 0.3}}]}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SEO keyword research expert. Generate realistic keyword data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        keywords = result.get("keywords", [])
        
        # Format for API response - return full pool for Quick Wins processing
        formatted_keywords = []
        for kw in keywords:  # Don't limit here, let Quick Wins service pick best ones
            formatted_keywords.append({
                "keyword": kw.get("keyword", ""),
                "volume": int(kw.get("volume", 0)),
                "cpc": float(kw.get("cpc", 0.0)),
                "competition": float(kw.get("competition", 0.0)),
                "source": "AI-Generated"
            })
        
        return formatted_keywords
        
    except Exception as e:
        # If AI generation fails, return basic fallback
        return generate_basic_keywords_fallback(topic, max_results)


def load_keywords_from_csv(topic: str, max_results: int = 20):
    """Fallback method using CSV data."""
    if not GKP_PATH.exists():
        return generate_basic_keywords_fallback(topic, max_results)
        
    df = pd.read_csv(GKP_PATH)
    df["Keyword"] = df["Keyword"].astype(str).str.lower()
    filtered = df[df["Keyword"].str.contains(topic.lower(), na=False)]
    
    if filtered.empty:
        # If no matches in CSV, generate basic keywords
        return generate_basic_keywords_fallback(topic, max_results)
        
    filtered = filtered.sort_values(by="Search Volume", ascending=False)
    rows = filtered.head(max_results)
    out = []
    for _, r in rows.iterrows():
        out.append({
            "keyword": r.get("Keyword"),
            "volume": int(r.get("Search Volume", 0)) if pd.notna(r.get("Search Volume")) else None,
            "cpc": float(r.get("CPC", 0)) if pd.notna(r.get("CPC")) else None,
            "competition": float(r.get("Competition", 0)) if pd.notna(r.get("Competition")) else None,
            "source": "GKP",
        })
    return out


def generate_basic_keywords_fallback(topic: str, max_results: int = 20):
    """Generate basic keyword variations when all else fails."""
    base_modifiers = [
        "best", "cheap", "affordable", "top", "reviews", "buy", "online",
        "near me", "for sale", "price", "cost", "how to", "guide", 
        "tips", "2024", "professional", "quality"
    ]
    
    keywords = []
    
    # Add the main topic
    keywords.append({
        "keyword": topic.lower(),
        "volume": 2500,
        "cpc": 1.20,
        "competition": 0.4,
        "source": "Generated"
    })
    
    # Generate variations with modifiers
    for modifier in base_modifiers[:max_results-1]:
        if modifier in ["how to", "guide", "tips"]:
            kw = f"{modifier} {topic.lower()}"
        elif modifier in ["2024"]:
            kw = f"{topic.lower()} {modifier}"
        else:
            kw = f"{modifier} {topic.lower()}"
            
        # Generate realistic but varied metrics
        volume = max(100, 3000 - (len(keywords) * 150))
        cpc = 0.5 + (len(keywords) * 0.1)
        competition = 0.2 + (len(keywords) * 0.02)
        
        keywords.append({
            "keyword": kw,
            "volume": volume,
            "cpc": round(cpc, 2),
            "competition": round(min(competition, 0.9), 2),
            "source": "Generated"
        })
    
    return keywords[:max_results]


# GPT-powered analysis functions (paid only)
ANALYSIS_SYSTEM = (
    "You are an SEO strategist. You output STRICT JSON only - no prose."
)


def identify_quick_wins(keywords: List[Dict], max_results: int = 5) -> List[str]:
    """Identify Quick Win keywords using improved winnability algorithm.

    This is the base pass (strict thresholds). For a guaranteed set that can
    widen thresholds and expand variations when needed, use
    `guarantee_quick_wins` below.
    """
    candidates = _select_quick_wins(
        keywords,
        comp_max=0.4,
        vol_min=200,
        score_min=30,
        long_tail_min=None,
        require_modifier=False,
    )
    candidates_sorted = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return [kw["keyword"] for kw in candidates_sorted[:max_results]]


def compute_opportunity_score(keyword_text: str, volume: Optional[int], competition: Optional[float]) -> float:
    """Compute a consistent opportunity score used across API and UI."""
    if not volume or volume <= 0:
        return 0.0
    if competition is None:
        competition = 1.0
    volume_score = min(volume / 1000, 10)  # Cap influence of very high volume
    competition_penalty = competition * competition  # Quadratic penalty
    word_count = len((keyword_text or "").split())
    long_tail_bonus = 1.2 if word_count >= 4 else 1.0
    return (volume_score * (1 - competition_penalty) * long_tail_bonus) * 100.0


def annotate_keywords_with_scores(keywords: List[Dict]) -> List[Dict]:
    """Add opportunity_score and is_quick_win flags to each keyword item.

    - opportunity_score: int 0-100+ (rounded)
    - is_quick_win: bool based on the strict pass thresholds
    """
    annotated: List[Dict] = []
    for kw in keywords:
        k = dict(kw)
        score = compute_opportunity_score(k.get("keyword", ""), k.get("volume"), k.get("competition"))
        k["opportunity_score"] = int(round(score))
        # Strict pass criteria for the badge
        comp = k.get("competition", 1.0) or 1.0
        vol = k.get("volume", 0) or 0
        k["is_quick_win"] = bool(comp <= 0.4 and vol >= 200 and score >= 30)
        annotated.append(k)
    return annotated


def guarantee_quick_wins(
    topic: str,
    keywords: List[Dict],
    min_results: int = 3,
    max_results: int = 5,
) -> List[str]:
    """Return at least `min_results` Quick Win keywords where possible.

    Strategy:
    1) Strict pass (same as identify_quick_wins)
    2) Relaxed thresholds if needed
    3) Deterministic long-tail expansion if still insufficient
    """
    # Pass 1 (strict)
    cands = _select_quick_wins(keywords, 0.4, 200, 30)

    # Pass 2 (wider)
    if len(cands) < min_results:
        cands = _dedupe_candidates(
            cands
            + _select_quick_wins(keywords, 0.5, 120, 20, long_tail_min=4)
        )

    # Pass 3 (widest)
    if len(cands) < min_results:
        cands = _dedupe_candidates(
            cands
            + _select_quick_wins(
                keywords, 0.55, 80, 15, long_tail_min=4, require_modifier=True
            )
        )

    # Expansion (deterministic, no model calls)
    if len(cands) < min_results:
        expanded = expand_long_tail_variations(topic)
        cands = _dedupe_candidates(
            cands
            + _select_quick_wins(
                expanded, 0.55, 80, 15, long_tail_min=4, require_modifier=True
            )
        )

    # Sort and trim
    cands_sorted = sorted(cands, key=lambda x: x["score"], reverse=True)
    if not cands_sorted:
        # Final fallback: pick top by score from original list
        scored = [
            {
                "keyword": k.get("keyword", ""),
                "score": compute_opportunity_score(
                    k.get("keyword", ""), k.get("volume"), k.get("competition")
                ),
            }
            for k in keywords
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return [x["keyword"] for x in scored[:min(max_results, 3)]]
    return [kw["keyword"] for kw in cands_sorted[:max_results]]


def _select_quick_wins(
    keywords: List[Dict],
    comp_max: float,
    vol_min: int,
    score_min: float,
    long_tail_min: Optional[int] = None,
    require_modifier: bool = False,
) -> List[Dict]:
    """Filter and score keywords that meet the provided thresholds."""
    MODIFIERS = [
        "under", "budget", "cheap", "affordable", "near me", "for", "best",
        "reviews", "vs", "guide", "tips"
    ]
    out: List[Dict] = []
    for kw in keywords:
        text = kw.get("keyword", "") or ""
        vol = kw.get("volume", 0) or 0
        comp = kw.get("competition", 1.0)
        if comp is None:
            comp = 1.0
        if vol < vol_min or comp > comp_max:
            continue
        words = len(text.split())
        if long_tail_min and words < long_tail_min:
            continue
        if require_modifier and not any(m in text.lower() for m in MODIFIERS):
            continue
        score = compute_opportunity_score(text, vol, comp)
        if score < score_min:
            continue
        out.append({
            "keyword": text,
            "score": score,
            "volume": vol,
            "competition": comp,
        })
    return out


def _dedupe_candidates(cands: List[Dict]) -> List[Dict]:
    seen = set()
    out: List[Dict] = []
    for c in cands:
        k = c.get("keyword", "")
        if k and k not in seen:
            seen.add(k)
            out.append(c)
    return out


def expand_long_tail_variations(topic: str, max_results: int = 24) -> List[Dict]:
    """Create deterministic long-tail variations without model calls.

    Produces realistic metrics with a bias toward winnable terms.
    """
    topic_lower = (topic or "").strip().lower()
    if not topic_lower:
        return []
    price_mods = ["under $50", "under $100", "budget", "affordable"]
    use_cases = ["for zoom calls", "for podcasting", "for interviews", "for beginners"]
    specs = ["usb", "xlr", "wireless", "noise cancelling"]
    geo = ["near me"]
    patterns = []
    for p in price_mods:
        patterns.append(f"{topic_lower} {p}")
    for u in use_cases:
        patterns.append(f"{topic_lower} {u}")
    for s in specs:
        patterns.append(f"best {s} {topic_lower}")
    for g in geo:
        patterns.append(f"{topic_lower} {g}")

    items: List[Dict] = []
    for i, text in enumerate(patterns[:max_results], start=1):
        # Deterministic metrics: decreasing volume, moderate CPC, moderate-low comp
        volume = max(80, 900 - i * 30)
        cpc = round(0.6 + (i % 5) * 0.12, 2)
        comp = round(0.22 + (i % 7) * 0.04, 2)
        items.append({
            "keyword": text,
            "volume": volume,
            "cpc": cpc,
            "competition": min(comp, 0.6),
            "source": "Generated",
        })
    return items


def build_analysis_prompt(gkp_items: List[Dict]) -> str:
    # reduce payload size for the model
    rows = [
        {
            "keyword": i.get("keyword"),
            "volume": i.get("volume"),
            "cpc": i.get("cpc"),
            "competition": i.get("competition"),
        }
        for i in gkp_items
    ]
    return (
        "Given this keyword list with volume, CPC, and competition, "
        "1) cluster them by intent (informational/commercial/navigational), "
        "2) identify the TOP Quick Win keywords (low competition 0.1-0.4, decent volume 200+, high opportunity), "
        "and 3) provide actionable SEO strategy notes.\n\n"
        "QUICK WINS CRITERIA:\n"
        "- Competition: 0.1-0.4 (low to medium-low)\n"
        "- Volume: 200+ monthly searches\n"
        "- Long-tail keywords (3+ words) preferred\n"
        "- Focus on keywords you can realistically rank for\n\n"
        "Return JSON with keys: clusters, quick_wins, notes.\n\n"
        f"keywords={json.dumps(rows, ensure_ascii=False)}"
    )


def analyze_keywords_with_gpt(gkp_items: List[Dict], model: str) -> Dict:
    prompt = build_analysis_prompt(gkp_items)
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"}  # enforce JSON
    )
    txt = resp.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        # Fallback: minimal payload if model misbehaves
        return {"clusters": [], "quick_wins": [], "notes": "Could not parse JSON"}
