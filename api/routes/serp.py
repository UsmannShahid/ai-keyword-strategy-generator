from fastapi import APIRouter
from ..models.schemas import SerpRequest, SerpResponse
from ..core.config import get_settings
from ..core.serp import fetch_serp

router = APIRouter(tags=["serp"])

@router.post("/", response_model=SerpResponse)
def get_serp(payload: SerpRequest):
    settings = get_settings(payload.user_plan)
    data = fetch_serp(payload.keyword, provider=settings["serp_provider"])
    return SerpResponse(serp=data)
