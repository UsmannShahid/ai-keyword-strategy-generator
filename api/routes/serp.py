from fastapi import APIRouter, HTTPException
from ..models.schemas import SerpRequest, SerpResponse
from ..core.config import get_settings
from ..core.serp import fetch_serp
from ..core.gpt import analyze_serp_data
from api.core.usage import consume_quota
from src.analytics import log_event, TimedContext
from ..db import get_serp_cache, set_serp_cache, init_serp_cache_table

router = APIRouter(tags=["serp"])

@router.post("/", response_model=SerpResponse)
def get_serp(payload: SerpRequest):
    settings = get_settings(payload.user_plan)
    
    # Initialize SERP cache table if not exists
    init_serp_cache_table()

    event_type = "serp_query"
    endpoint = "/serp"
    
    try:
        # Check cache first (24 hour TTL for database cache)
        cached_data = get_serp_cache(
            keyword=payload.keyword,
            country=payload.country, 
            language=payload.language,
            ttl_hours=24
        )
        
        if cached_data and cached_data.get("from_cache"):
            # Return cached data without consuming quota
            log_event(
                user_id=payload.user_id,
                plan=payload.user_plan,
                event_type=f"{event_type}_cached",
                endpoint=endpoint,
                keyword=payload.keyword,
                latency_ms=0,
                success=True,
            )
            
            # Get current quota remaining for meta
            _, remaining = consume_quota(payload.user_id, payload.user_plan, "serp_query", 0)
            
            response_data = {
                "serp": cached_data.get("serp"), 
                "analysis": {
                    "search_intent": cached_data.get("search_intent"),
                    "difficulty_score": cached_data.get("difficulty_score"),
                    "competition_analysis": cached_data.get("competition_analysis")
                } if cached_data.get("search_intent") else None,
                "meta": {
                    "remaining": {"serp_query": remaining},
                    "from_cache": True,
                    "cached_at": cached_data.get("cached_at")
                }
            }
            return SerpResponse(**response_data)

        # Not in cache, consume quota and fetch fresh data
        success, remaining = consume_quota(payload.user_id, payload.user_plan, "serp_query", 1)
        if not success:
            raise HTTPException(status_code=402, detail="SERP quota exceeded. Upgrade or wait until next month.")

        with TimedContext() as t:
            data = fetch_serp(
                payload.keyword, 
                provider=settings["serp_provider"],
                country=payload.country,
                language=payload.language
            )
            
            # Extract organic results for caching
            organic_results = data.get("organic", [])[:10] if data else []
            
            # Add competitive analysis for paid plans
            analysis = None
            search_intent = None
            difficulty_score = None
            competition_analysis = None
            
            if payload.user_plan == "paid" and data and organic_results:
                try:
                    analysis = analyze_serp_data(
                        payload.keyword, 
                        organic_results, 
                        settings["gpt_model"]
                    )
                    # Extract analysis components for caching
                    if analysis:
                        search_intent = analysis.get("search_intent")
                        difficulty_score = analysis.get("difficulty_score")
                        competition_analysis = analysis.get("competition_analysis")
                except Exception:
                    # If analysis fails, continue without it
                    pass
            
            # Cache the results
            try:
                set_serp_cache(
                    keyword=payload.keyword,
                    country=payload.country,
                    language=payload.language,
                    serp_data=data,
                    organic_results=organic_results,
                    search_intent=search_intent,
                    competition_analysis=competition_analysis,
                    difficulty_score=difficulty_score
                )
            except Exception as cache_e:
                # Cache errors shouldn't break the API
                print(f"Cache write failed: {cache_e}")
            
        # Log successful API call
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            latency_ms=t.elapsed_ms,
            success=True,
        )
        
        response_data = {
            "serp": data, 
            "analysis": analysis,
            "meta": {
                "remaining": {"serp_query": remaining},
                "from_cache": False
            }
        }
        return SerpResponse(**response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions (like quota exceeded)
        raise
    except Exception as e:
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            success=False,
            error=str(e)[:2000],
        )
        raise HTTPException(status_code=500, detail=f"SERP fetch failed: {str(e)}")
