# ai_keyword_tool/scoring.py
from __future__ import annotations
import re
from typing import Iterable
import pandas as pd
from typing import Dict, Any
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

# Breakdown Helper
def quickwin_breakdown(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a consistent breakdown dict for a keyword row.
    Expected row keys (best effort): 'Keyword','Volume','Intent','QW Score','SERP_weak_forum','SERP_weak_thin','SERP_weak_old'
    """
    kw = row.get("Keyword") or row.get("keyword") or ""
    score = float(row.get("QW Score", 0) or 0)
    vol = int(row.get("Volume", 0) or 0)
    intent = (row.get("Intent") or "").lower()

    # If you already compute sub-scores, plug them here; otherwise do simple proxies:
    subs = {
        "volume_score": min(100, (vol / 1000) * 100) if vol else 0,  # naive proxy
        "intent_boost": 20 if any(w in intent for w in ["transaction", "buyer", "commercial"]) else (10 if "info" in intent else 0),
        "serp_weakness": 0,  # fill from SERP snapshot if available
    }

    # Optionally fill weakness from cached SERP summary on the row
    weak_forum = 1 if row.get("SERP_weak_forum") else 0
    weak_thin  = 1 if row.get("SERP_weak_thin")  else 0
    weak_old   = 1 if row.get("SERP_weak_old")   else 0
    subs["serp_weakness"] = (weak_forum + weak_thin + weak_old) * 10  # naive 0–30

    return {
        "keyword": kw,
        "score": round(score, 1),
        "volume": vol,
        "intent": intent or "unknown",
        "subscores": subs,
        "weak_flags": {
            "forum": bool(weak_forum),
            "thin":  bool(weak_thin),
            "old":   bool(weak_old),
        },
    }

def explain_quickwin(breakdown: Dict[str, Any]) -> str:
    """Plain-English explanation from the breakdown dict."""
    kw = breakdown["keyword"]
    s  = breakdown["score"]
    vol = breakdown["volume"]
    intent = breakdown["intent"]
    subs = breakdown["subscores"]
    weak = breakdown["weak_flags"]

    reasons = []
    if vol: reasons.append(f"decent search volume (~{vol}/mo)")
    if subs["intent_boost"] >= 20: reasons.append("strong buyer/transactional intent")
    elif "info" in intent: reasons.append("clear informational intent")
    if subs["serp_weakness"] >= 10:
        weak_bits = [name for name, v in weak.items() if v]
        if weak_bits:
            reasons.append("SERP weak spots: " + ", ".join(weak_bits))

    if not reasons:
        reasons.append("limited signals; consider broader modifiers or adjacent topics")

    verdict = "good quick win" if s >= 70 else ("promising but needs angle" if s >= 50 else "likely hard to win now")
    return f"“{kw}” looks {verdict} because: " + "; ".join(reasons) + "."
