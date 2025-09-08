# api/core/config.py
from typing import Literal, Dict

PlanType = Literal["free", "paid"]

PLAN_CONFIG: Dict[PlanType, dict] = {
    "free": {
        "gpt_model": "gpt-3.5-turbo",
        "serp_provider": "serper",     # free/dev provider
        "keyword_analysis_enabled": False,
        "max_keyword_results": 10,
    },
    "paid": {
        "gpt_model": "gpt-4o-mini",       # supports JSON mode
        "serp_provider": "searchapi",
        "keyword_analysis_enabled": True,
        "max_keyword_results": 25,
    },
}

def get_settings(user_plan: PlanType) -> dict:
    if user_plan not in PLAN_CONFIG:
        user_plan = "free"
    return PLAN_CONFIG[user_plan]

# Per-plan monthly quotas for actions
PLAN_QUOTAS = {
    "free": {
        "brief_create": 3,      # per month
        "serp_query": 30,
        "kw_suggest": 50,       # GKP reads (cheap)
        "product_description": 0,
        "strategy_create": 2,   # comprehensive strategies
    },
    "paid": {
        "brief_create": 50,
        "serp_query": 100,
        "kw_suggest": 200,
        "product_description": 100,
        "strategy_create": 25,
    },
    # future: "premium": {...}
}
