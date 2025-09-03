from fastapi import APIRouter, HTTPException
from api.models.schemas import ProductDescriptionRequest, ProductDescriptionResponse
from api.core.config import get_settings
from api.core.gpt import generate_product_description

router = APIRouter(tags=["product"])

@router.post("/", response_model=ProductDescriptionResponse)
def create_product_description(payload: ProductDescriptionRequest):
    settings = get_settings(payload.user_plan)

    # Free plan block
    if payload.user_plan == "free":
        return ProductDescriptionResponse(
            title=payload.product_name,
            bullets=payload.features,
            description="Upgrade to Pro to unlock ecommerce product descriptions.",
            seo_keywords=[],
            notes="Available only on paid plans."
        )

    # Paid plan → GPT generation
    try:
        result = generate_product_description(
            product_name=payload.product_name,
            features=payload.features,
            channel=payload.channel,
            tone=payload.tone,
            length=payload.length,
            model=settings["gpt_model"],
        )
        return ProductDescriptionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product description generation failed: {str(e)}")
