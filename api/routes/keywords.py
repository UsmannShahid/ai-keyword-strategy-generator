# api/routes/keywords.py
from fastapi import APIRouter
from ..models.schemas import SuggestKeywordsRequest, SuggestKeywordsResponse, KeywordItem
from ..core.config import get_settings
from ..core.keywords import load_gkp_keywords

router = APIRouter(tags=["keywords"])

@router.post("/", response_model=SuggestKeywordsResponse)
def suggest_keywords(payload: SuggestKeywordsRequest):
    settings = get_settings(payload.user_plan)
    limit = min(payload.max_results, settings["max_keyword_results"])
    items = load_gkp_keywords(payload.topic, limit=limit)
    # For now: no AI clustering (added in a later step)
    return SuggestKeywordsResponse(keywords=[KeywordItem(**i) for i in items])
