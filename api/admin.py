import os
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from src.analytics import get_summary, get_top_users, get_funnel

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])
ADMIN_KEY = os.getenv("ADMIN_KEY")


def admin_guard(x_admin_key: str | None = Header(default=None, convert_underscores=False)):
    # Allow all if ADMIN_KEY not set (local dev)
    if not ADMIN_KEY:
        return True
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@router.get("/summary")
def summary(days: int = Query(30, ge=1, le=365), _=Depends(admin_guard)):
    return get_summary(days)


@router.get("/users")
def users(days: int = Query(30, ge=1, le=365), limit: int = Query(20, ge=1, le=200), _=Depends(admin_guard)):
    return {"items": get_top_users(limit=limit, days=days)}


@router.get("/funnel")
def funnel(days: int = Query(30, ge=1, le=365), _=Depends(admin_guard)):
    return get_funnel(days)

