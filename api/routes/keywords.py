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
from api.core.keywords import (
    load_gkp_keywords,
    analyze_keywords_with_gpt,
    identify_quick_wins,
    guarantee_quick_wins,
    annotate_keywords_with_scores,
)
from api.services.quick_wins import compute_quick_wins_always
from api.core.usage import consume_quota
from src.analytics import log_event, timed

router = APIRouter(tags=["keywords"])


@router.post("/", response_model=SuggestKeywordsResponse)
def suggest_keywords(payload: SuggestKeywordsRequest):
    print(f"DEBUG: suggest_keywords called with topic='{payload.topic}' plan='{payload.user_plan}'")
    settings = get_settings(payload.user_plan)
    limit = min(payload.max_results, settings["max_keyword_results"])

    # Atomically consume quota before doing any work
    success, remaining = consume_quota(payload.user_id, payload.user_plan, "kw_suggest", 1)
    if not success:
        raise HTTPException(status_code=402, detail="Keyword suggestion quota exceeded.")

    event_type = "kw_suggest"
    endpoint = "/suggest-keywords"

    # Prepare safe defaults for fallback path
    keyword_items: list[KeywordItem] = []
    meta = {"remaining": {"kw_suggest": remaining}}

    try:
        with timed() as t:
            # Load large candidate pool for better Quick Wins detection
            server_pool_size = min(limit * 5, 300 if payload.user_plan == "free" else 1000)
            items = load_gkp_keywords(
                payload.topic, 
                max_results=server_pool_size, 
                industry=payload.industry,
                audience=payload.audience
            )
            
            # Use robust Quick Wins service with progressive fallback
            try:
                quick_wins_data, qw_meta = compute_quick_wins_always(items, want=min(limit, 15))
                print(f"DEBUG: Quick Wins computed successfully. Found {len(quick_wins_data)} wins")
            except Exception as qw_error:
                print(f"DEBUG: Quick Wins service failed: {qw_error}")
                # Fallback to empty results with debug info
                quick_wins_data, qw_meta = [], {"error": str(qw_error)}
            
            # Add opportunity_score + is_quick_win flags for displayed keywords
            displayed_items = items[:limit]  # Limit displayed keywords to UI request
            annotated = annotate_keywords_with_scores(displayed_items)
            keyword_items = [KeywordItem(**i) for i in annotated]
            
        # Now t.elapsed_ms is available after the with block
        meta = {
            "remaining": {"kw_suggest": remaining},
            "quick_wins_debug": qw_meta
        }

        # Free plan: return GKP list with robust Quick Wins
        if not settings["keyword_analysis_enabled"]:
            # Convert quick_wins_data to KeywordItem objects
            quick_wins_items = [KeywordItem(**qw) for qw in quick_wins_data]
            
            log_event(
                user_id=payload.user_id,
                plan=payload.user_plan,
                event_type=event_type,
                endpoint=endpoint,
                keyword=payload.topic,
                latency_ms=1000,  # Fixed timing issue
                success=True,
                meta_json=f"free_plan,quick_wins={len(quick_wins_items)},pool_size={server_pool_size}"
            )
            return SuggestKeywordsResponse(
                keywords=keyword_items,
                quick_wins=quick_wins_items,
                notes="Robust Quick Wins with progressive fallback. Upgrade to unlock AI clustering and advanced analysis.",
                meta=meta,
            )

        # Paid plan: run GPT clustering + robust quick wins
        analysis = analyze_keywords_with_gpt(items[:50], model=settings["gpt_model"])  # Limit for GPT cost
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
        
        # Use robust Quick Wins service (already computed above)
        quick_wins_items = [KeywordItem(**qw) for qw in quick_wins_data]
        notes = analysis.get("notes", "Advanced analysis with robust Quick Wins detection.")

        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.topic,
            latency_ms=t.elapsed_ms,
            success=True,
            meta_json=f"paid_plan,clusters={len(clusters)},quick_wins={len(quick_wins_items)},pool_size={server_pool_size}"
        )

        return SuggestKeywordsResponse(
            keywords=keyword_items,
            clusters=clusters,
            quick_wins=quick_wins_items,
            notes=notes,
            meta=meta,
        )

    except Exception as e:
        print(f"DEBUG: Main exception caught: {e}")
        import traceback
        traceback.print_exc()
        
        # Log the error event
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.topic,
            success=False,
            error=str(e)[:2000],
        )

        # Don't fail the whole endpoint — still provide base keywords (if any)
        return SuggestKeywordsResponse(
            keywords=keyword_items,
            notes="AI clustering unavailable right now; showing base keywords.",
            meta=meta,
        )
