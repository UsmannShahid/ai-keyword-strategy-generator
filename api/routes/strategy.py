from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from ..core.config import get_settings
from ..core.gpt import generate_comprehensive_strategy
from api.core.usage import consume_quota
from src.analytics import log_event, timed

router = APIRouter(tags=["strategy"])

class StrategyRequest(BaseModel):
    keyword: str
    brief: dict
    serp_results: list
    serp_analysis: Optional[dict] = None
    user_id: str = "dev-user"
    user_plan: str = "free"

class StrategyResponse(BaseModel):
    strategy: dict
    meta: Optional[dict] = None

@router.post("/", response_model=StrategyResponse)
def generate_strategy(payload: StrategyRequest):
    settings = get_settings(payload.user_plan)

    # Atomically consume quota before doing any work
    success, remaining = consume_quota(payload.user_id, payload.user_plan, "strategy_create", 1)
    if not success:
        raise HTTPException(status_code=402, detail="Strategy quota exceeded. Upgrade or wait until next month.")

    event_type = "strategy_create"
    endpoint = "/strategy"

    try:
        with timed() as t:
            strategy_data = generate_comprehensive_strategy(
                keyword=payload.keyword,
                brief=payload.brief,
                serp_results=payload.serp_results,
                serp_analysis=payload.serp_analysis or {},
                model=settings["gpt_model"]
            )
            if not strategy_data:
                raise HTTPException(status_code=502, detail="Empty strategy from model")
        
        # Log successful event
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            latency_ms=t.elapsed_ms,
            success=True,
        )
        
        return StrategyResponse(
            strategy=strategy_data,
            meta={"remaining": {"strategy_create": remaining}},
        )
    except HTTPException:
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            success=False,
            error="HTTPException",
        )
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
        detail = "Missing OPENAI_API_KEY" if "OPENAI_API_KEY" in str(e) else "Strategy generation failed"
        raise HTTPException(status_code=500, detail=detail)