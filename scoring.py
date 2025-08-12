# ai_keyword_tool/scoring.py
from __future__ import annotations
import re
from typing import Iterable
import pandas as pd

# Common commercial/action modifiers that signal purchase or strong intent
MODIFIERS = {
    "buy","price","pricing","cost","cheap","affordable","discount","deal","vs","compare","comparison",
    "best","top","review","alternative","alternatives","near me","near","for","software","tool",
    "integrate","integration","tutorial","how to","setup","template","example"
}

def is_long_tail(kw: str) -> bool:
    return len(kw.split()) >= 3

def has_modifier(kw: str) -> bool:
    k = kw.lower()
    return any(m in k for m in MODIFIERS)

def guess_competition_score(kw: str) -> int:
    """
    Heuristic 'competition' (0 = easier, 100 = harder), derived from keyword shape.
    Short, head terms tend to be more competitive; long-tail with modifiers less so.
    """
    score = 50
    # Head terms are harder
    if len(kw.split()) <= 2:
        score += 20
    else:
        score -= 10
    # Modifiers often reduce competition (niche/intent)
    if has_modifier(kw):
        score -= 10
    # Brand-like tokens often increase competition unless it’s the user’s brand (unknown here)
    if re.search(r"\b(amazon|google|microsoft|shopify|wordpress|ahrefs|semrush)\b", kw, re.I):
        score += 10
    # Clamp
    return max(0, min(100, score))

def opportunity_from_row(keyword: str, intent: str) -> int:
    """
    Compute a 0–100 opportunity score using simple, transparent rules:
    Base 50, then adjust with intent, long-tail, modifiers, and heuristic competition.
    """
    base = 50
    # Intent weighting
    if intent in ("transactional", "commercial"):
        base += 10
    elif intent in ("informational",):
        base += 5
    elif intent in ("branded",):
        base -= 10
    elif intent in ("navigational",):
        base -= 5

    # Shape signals
    if is_long_tail(keyword):
        base += 10
    if has_modifier(keyword):
        base += 10

    # Competition inverse: lower comp → higher opp
    comp = guess_competition_score(keyword)
    base += int((50 - comp) * 0.4)  # scale inverse comp influence

    # Clamp
    return int(max(0, min(100, base)))

def add_scores(df: pd.DataFrame, intent_col: str = "category", kw_col: str = "keyword") -> pd.DataFrame:
    """
    Returns a new DataFrame with `opportunity` (0–100) and `priority` (1 = highest).
    `category` is treated as intent; rename if your column differs.
    """
    if df.empty or kw_col not in df.columns or intent_col not in df.columns:
        return df.assign(opportunity=[], priority=[])
    scored = df.copy()
    scored["opportunity"] = [
        opportunity_from_row(k, str(i).lower()) for k, i in zip(scored[kw_col], scored[intent_col])
    ]
    # Highest opportunity gets priority 1
    scored = scored.sort_values(by=["opportunity", kw_col], ascending=[False, True]).reset_index(drop=True)
    scored["priority"] = range(1, len(scored) + 1)
    # Restore original order for display, but keep the new cols
    scored = scored.reindex(sorted(scored.index), copy=False)
    return scored
