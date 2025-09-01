# api/routes/brief.py
from fastapi import APIRouter, HTTPException
from ..models.schemas import GenerateBriefRequest, GenerateBriefResponse
from ..core.config import get_settings
from ..core.gpt import generate_brief

router = APIRouter(tags=["brief"])

@router.post("/", response_model=GenerateBriefResponse)
def create_brief(payload: GenerateBriefRequest):
    try:
        settings = get_settings(payload.user_plan)
        brief_text = generate_brief(payload.keyword, model=settings["gpt_model"])
        if not brief_text:
            raise HTTPException(status_code=502, detail="Empty brief from model")
        return GenerateBriefResponse(brief=brief_text)
    except HTTPException:
        raise
    except Exception as e:
        # Don't leak internals to client; log later.
        detail = "Missing OPENAI_API_KEY" if "OPENAI_API_KEY" in str(e) else "Brief generation failed"
        raise HTTPException(status_code=500, detail=detail)

