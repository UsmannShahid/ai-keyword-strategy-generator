from fastapi import APIRouter, HTTPException
from ..models.schemas import SerpRequest, SerpResponse
from ..core.config import get_settings
from ..core.serp import fetch_serp
from api.core.usage import check_quota, log_usage

router = APIRouter(tags=["serp"])

@router.post("/", response_model=SerpResponse)
def get_serp(payload: SerpRequest):
    settings = get_settings(payload.user_plan)

    allowed, remaining = check_quota(payload.user_id, payload.user_plan, "serp_query", 1)
    if not allowed:
        raise HTTPException(status_code=402, detail="SERP quota exceeded. Upgrade or wait until next month.")

    data = fetch_serp(payload.keyword, provider=settings["serp_provider"])
    log_usage(payload.user_id, "serp_query", 1)
    return SerpResponse(serp=data, meta={"remaining": {"serp_query": remaining - 1}})
