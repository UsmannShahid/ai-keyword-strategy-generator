"""Keyword suggestion endpoint with quota enforcement."""
from fastapi import APIRouter, HTTPException
from api.models.schemas import (
    SuggestKeywordsRequest,
    SuggestKeywordsResponse,
    KeywordItem,
    ClusterGroup,
    ClusterKeyword,
)
from api.core.config import get_settings
from api.core.keywords import load_gkp_keywords, analyze_keywords_with_gpt
from api.core.usage import check_quota, log_usage

router = APIRouter(tags=["keywords"])


@router.post("/", response_model=SuggestKeywordsResponse)
def suggest_keywords(payload: SuggestKeywordsRequest):
    settings = get_settings(payload.user_plan)
    limit = min(payload.max_results, settings["max_keyword_results"])

    allowed, remaining = check_quota(payload.user_id, payload.user_plan, "kw_suggest", 1)
    if not allowed:
        raise HTTPException(status_code=402, detail="Keyword suggestion quota exceeded.")

    items = load_gkp_keywords(payload.topic, limit=limit)
    keyword_items = [KeywordItem(**i) for i in items]
    meta = {"remaining": {"kw_suggest": remaining - 1}}
    log_usage(payload.user_id, "kw_suggest", 1)

    # Free plan: return plain GKP list
    if not settings["keyword_analysis_enabled"]:
        return SuggestKeywordsResponse(
            keywords=keyword_items,
            notes="Upgrade to unlock AI clustering and Quick Wins.",
            meta=meta,
        )

    # Paid plan: run GPT clustering + quick wins
    try:
        analysis = analyze_keywords_with_gpt(items, model=settings["gpt_model"])
        # Normalize clusters into schema
        clusters = []
        for c in analysis.get("clusters", []):
            groups_keywords = [
                ClusterKeyword(keyword=k if isinstance(k, str) else k.get("keyword", ""))
                for k in c.get("keywords", [])
            ]
            clusters.append(
                ClusterGroup(
                    name=c.get("name", "Cluster"),
                    intent=c.get("intent", "informational"),
                    keywords=groups_keywords,
                )
            )
        quick_wins = [
            kw if isinstance(kw, str) else kw.get("keyword", "") for kw in analysis.get("quick_wins", [])
        ]
        notes = analysis.get("notes")
        return SuggestKeywordsResponse(
            keywords=keyword_items,
            clusters=clusters,
            quick_wins=quick_wins,
            notes=notes,
            meta=meta,
        )
    except Exception:
        # Don't fail the whole endpoint—still provide base keywords
        return SuggestKeywordsResponse(
            keywords=keyword_items,
            notes="AI clustering unavailable right now; showing base keywords.",
            meta=meta,
        )

