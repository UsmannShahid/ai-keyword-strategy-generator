from fastapi import APIRouter, HTTPException
from ..models.schemas import SerpRequest, SerpResponse
from ..core.config import get_settings
from ..core.serp import fetch_serp
from ..core.gpt import analyze_serp_data
from api.core.usage import consume_quota
from src.analytics import log_event, timed

router = APIRouter(tags=["serp"])

@router.post("/", response_model=SerpResponse)
def get_serp(payload: SerpRequest):
    settings = get_settings(payload.user_plan)

    # Atomically consume quota before doing any work
    success, remaining = consume_quota(payload.user_id, payload.user_plan, "serp_query", 1)
    if not success:
        raise HTTPException(status_code=402, detail="SERP quota exceeded. Upgrade or wait until next month.")

    event_type = "serp_query"
    endpoint = "/serp"
    try:
        with timed() as t:
            data = fetch_serp(
                payload.keyword, 
                provider=settings["serp_provider"],
                country=payload.country,
                language=payload.language
            )
            
            # Add competitive analysis for paid plans
            analysis = None
            if payload.user_plan == "paid" and data and data.get("organic"):
                try:
                    analysis = analyze_serp_data(
                        payload.keyword, 
                        data.get("organic", []), 
                        settings["gpt_model"]
                    )
                except Exception:
                    # If analysis fails, continue without it
                    pass
            
        # No need to log_usage - already done atomically in consume_quota
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            tokens_est=None,
            latency_ms=t.elapsed_ms,
            success=True,
        )
        
        response_data = {
            "serp": data, 
            "analysis": analysis,
            "meta": {"remaining": {"serp_query": remaining}}
        }
        return SerpResponse(**response_data)
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
        raise
