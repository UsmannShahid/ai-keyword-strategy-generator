# api/routes/suggestions.py
from fastapi import APIRouter
from ..models.schemas import SuggestionsRequest, SuggestionsResponse
from ..core.gpt import generate_suggestions

router = APIRouter(tags=["suggestions"])

@router.post("/", response_model=SuggestionsResponse)
def suggest_content(payload: SuggestionsRequest):
    ideas = generate_suggestions(payload.brief, payload.serp)
    return SuggestionsResponse(ideas=ideas)
