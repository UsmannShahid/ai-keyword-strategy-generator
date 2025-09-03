from __future__ import annotations
import time
import os
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from sqlalchemy import (
    Table, Column, Integer, String, Boolean, Float, DateTime, Text, create_engine,
    MetaData, select, func, and_, distinct
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

# Use shared app_data.db by default
DB_URL = os.getenv("DB_URL", "sqlite:///app_data.db")
engine: Engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

# --- Events table ---
events = Table(
    "events", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ts", DateTime, nullable=False, default=datetime.utcnow, index=True),
    Column("user_id", String, nullable=True, index=True),
    Column("plan", String, nullable=True),
    Column("event_type", String, nullable=False, index=True),
    Column("endpoint", String, nullable=False),
    Column("keyword", String, nullable=True),
    Column("channel", String, nullable=True),
    Column("tokens_est", Integer, nullable=True),
    Column("latency_ms", Float, nullable=True),
    Column("success", Boolean, nullable=False, default=True),
    Column("error", Text, nullable=True),
    Column("meta_json", Text, nullable=True),
)

metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def log_event(
    *,
    user_id: Optional[str],
    plan: Optional[str],
    event_type: str,
    endpoint: str,
    keyword: Optional[str] = None,
    channel: Optional[str] = None,
    tokens_est: Optional[int] = None,
    latency_ms: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None,
    meta_json: Optional[str] = None,
) -> None:
    """Insert a single analytics event row."""
    with SessionLocal() as s:
        s.execute(
            events.insert().values(
                ts=datetime.utcnow(),
                user_id=user_id,
                plan=plan,
                event_type=event_type,
                endpoint=endpoint,
                keyword=keyword,
                channel=channel,
                tokens_est=tokens_est,
                latency_ms=latency_ms,
                success=success,
                error=error,
                meta_json=meta_json,
            )
        )
        s.commit()


class timed:
    """Context manager to measure elapsed milliseconds."""
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed_ms = (time.perf_counter() - self.t0) * 1000.0


def _daterange(days: int) -> Tuple[datetime, datetime]:
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return start, end


def get_summary(days: int = 30) -> Dict[str, Any]:
    start, end = _daterange(days)
    with SessionLocal() as s:
        base = select(events).where(and_(events.c.ts >= start, events.c.ts <= end))
        total = s.execute(select(func.count()).select_from(base.subquery())).scalar() or 0

        total_users = s.execute(
            select(func.count(distinct(events.c.user_id))).where(
                and_(events.c.ts >= start, events.c.ts <= end, events.c.user_id.isnot(None))
            )
        ).scalar() or 0

        paid_users = s.execute(
            select(func.count(distinct(events.c.user_id))).where(
                and_(
                    events.c.ts >= start, events.c.ts <= end,
                    events.c.user_id.isnot(None),
                    events.c.plan == "paid"
                )
            )
        ).scalar() or 0

        tokens_total = s.execute(
            select(func.coalesce(func.sum(events.c.tokens_est), 0)).where(
                and_(events.c.ts >= start, events.c.ts <= end)
            )
        ).scalar() or 0

        avg_latency = s.execute(
            select(func.avg(events.c.latency_ms)).where(
                and_(events.c.ts >= start, events.c.ts <= end, events.c.latency_ms.isnot(None))
            )
        ).scalar()

        def count_type(t: str) -> int:
            return s.execute(
                select(func.count()).where(
                    and_(
                        events.c.ts >= start, events.c.ts <= end,
                        events.c.event_type == t
                    )
                )
            ).scalar() or 0

        return {
            "window_days": days,
            "total_events": total,
            "total_users": total_users,
            "paid_users": paid_users,
            "paid_ratio": (paid_users / total_users) if total_users else 0.0,
            "counts": {
                "brief_create": count_type("brief_create"),
                "serp_query": count_type("serp_query"),
                "kw_suggest": count_type("kw_suggest"),
                "product_description": count_type("product_description"),
                "export": count_type("export"),
            },
            "tokens_total": int(tokens_total),
            "avg_latency_ms": float(avg_latency) if avg_latency is not None else None,
        }


def get_top_users(limit: int = 20, days: int = 30) -> List[Dict[str, Any]]:
    start, end = _daterange(days)
    with SessionLocal() as s:
        rows = s.execute(
            select(
                events.c.user_id,
                func.count().label("events_count"),
                func.coalesce(func.sum(events.c.tokens_est), 0).label("tokens"),
                func.max(events.c.plan).label("plan"),
            )
            .where(and_(events.c.ts >= start, events.c.ts <= end, events.c.user_id.isnot(None)))
            .group_by(events.c.user_id)
            .order_by(func.count().desc())
            .limit(limit)
        ).all()
    return [
        {"user_id": r.user_id, "events": r.events_count, "tokens": int(r.tokens), "plan": r.plan}
        for r in rows
    ]


def get_funnel(days: int = 30) -> Dict[str, Any]:
    """
    Funnel across the window:
      keyword -> brief -> serp -> suggestions -> export
    We count unique users who have at least one event in each stage.
    """
    start, end = _daterange(days)
    with SessionLocal() as s:
        def users_for(t: str) -> set:
            rows = s.execute(
                select(distinct(events.c.user_id)).where(
                    and_(
                        events.c.ts >= start, events.c.ts <= end,
                        events.c.user_id.isnot(None),
                        events.c.event_type == t
                    )
                )
            ).all()
            return {r[0] for r in rows if r[0] is not None}

        kw = users_for("kw_suggest")
        brief = users_for("brief_create")
        serp = users_for("serp_query")
        sugg = users_for("suggestions")
        export = users_for("export")

        def rate(numer: int, denom: int) -> float:
            return (numer / denom) if denom else 0.0

        return {
            "window_days": days,
            "stages_users": {
                "kw_suggest": len(kw),
                "brief_create": len(brief),
                "serp_query": len(serp),
                "suggestions": len(sugg),
                "export": len(export),
            },
            "conversions": {
                "kw→brief": rate(len(kw & brief), len(kw)),
                "brief→serp": rate(len(brief & serp), len(brief)),
                "serp→suggestions": rate(len(serp & sugg), len(serp)),
                "suggestions→export": rate(len(sugg & export), len(sugg)),
            }
        }

