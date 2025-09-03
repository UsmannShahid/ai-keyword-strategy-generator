# api/routes/brief.py
from fastapi import APIRouter, HTTPException
from ..models.schemas import GenerateBriefRequest, GenerateBriefResponse
from ..core.config import get_settings
from ..core.gpt import generate_brief
from api.core.usage import check_quota, log_usage

router = APIRouter(tags=["brief"])

@router.post("/", response_model=GenerateBriefResponse)
def create_brief(payload: GenerateBriefRequest):
    settings = get_settings(payload.user_plan)

    allowed, remaining = check_quota(payload.user_id, payload.user_plan, "brief_create", 1)
    if not allowed:
        raise HTTPException(status_code=402, detail="Brief quota exceeded. Upgrade or wait until next month.")

    try:
        brief_text = generate_brief(payload.keyword, model=settings["gpt_model"])
        if not brief_text:
            raise HTTPException(status_code=502, detail="Empty brief from model")
        log_usage(payload.user_id, "brief_create", 1)
        return GenerateBriefResponse(
            brief=brief_text,
            meta={"remaining": {"brief_create": remaining - 1}},
        )
    except HTTPException:
        raise
    except Exception as e:
        # Don't leak internals to client; log later.
        detail = "Missing OPENAI_API_KEY" if "OPENAI_API_KEY" in str(e) else "Brief generation failed"
        raise HTTPException(status_code=500, detail=detail)
