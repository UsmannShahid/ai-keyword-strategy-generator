from datetime import datetime
from calendar import monthrange
from api.db import get_conn
from api.core.config import PLAN_QUOTAS


def _month_bounds(dt: datetime):
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = monthrange(dt.year, dt.month)[1]
    end = dt.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    return start.isoformat(), end.isoformat()


def get_limit(plan: str, action: str) -> int:
    return PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"]).get(action, 0)


def get_used(user_id: str, action: str, now: datetime) -> int:
    start, end = _month_bounds(now)
    with get_conn() as conn:
        row = conn.execute(
            """
          SELECT COALESCE(SUM(qty),0) FROM usage_logs
          WHERE user_id=? AND action=? AND ts BETWEEN ? AND ?
        """,
            (user_id, action, start, end),
        ).fetchone()
        return int(row[0] or 0)


def check_quota(user_id: str, plan: str, action: str, need: int = 1):
    """Returns (allowed: bool, remaining: int)."""
    limit = get_limit(plan, action)
    used = get_used(user_id, action, datetime.utcnow())
    remaining = max(limit - used, 0)
    return (remaining >= need), remaining


def log_usage(user_id: str, action: str, qty: int = 1):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO usage_logs (user_id, action, qty, ts) VALUES (?, ?, ?, ?)",
            (user_id, action, qty, datetime.utcnow().isoformat()),
        )

