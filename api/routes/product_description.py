from fastapi import APIRouter, HTTPException
from api.models.schemas import ProductDescriptionRequest, ProductDescriptionResponse
from api.core.config import get_settings
from api.core.gpt import generate_product_description
from api.core.usage import check_quota, log_usage
from src.analytics import log_event, timed

router = APIRouter(tags=["product"])


@router.post("/", response_model=ProductDescriptionResponse)
def create_product_description(payload: ProductDescriptionRequest):
    settings = get_settings(payload.user_plan)
    event_type = "product_description"
    endpoint = "/product-description"

    # Free users: allowed to hit endpoint but constrained by quota/plan
    allowed, remaining = check_quota(payload.user_id, payload.user_plan, "product_description", 1)
    if not allowed:
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.product_name,
            channel=payload.channel,
            success=False,
            error="Quota exceeded"
        )
        return ProductDescriptionResponse(
            title=payload.product_name,
            bullets=payload.features,
            description="Upgrade to Pro to unlock ecommerce product descriptions.",
            seo_keywords=[],
            notes="Quota not available on your plan.",
            meta={"remaining": {"product_description": 0}},
        )

    try:
        with timed() as t:
            result = generate_product_description(
                product_name=payload.product_name,
                features=payload.features,
                channel=payload.channel,
                tone=payload.tone,
                length=payload.length,
                model=settings["gpt_model"],
            )
        
        log_usage(payload.user_id, "product_description", 1)
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.product_name,
            channel=payload.channel,
            latency_ms=t.elapsed_ms,
            success=True,
            meta_json=f"tone={payload.tone},length={payload.length}"
        )
        
        return ProductDescriptionResponse(
            **result, meta={"remaining": {"product_description": remaining - 1}}
        )
    except Exception as e:
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.product_name,
            channel=payload.channel,
            success=False,
            error=str(e)[:2000]
        )
        raise HTTPException(status_code=500, detail="Product description generation failed")

