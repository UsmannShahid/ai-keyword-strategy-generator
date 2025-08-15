# serp_utils.py
from __future__ import annotations
from typing import List, Dict, Any
import re
from urllib.parse import urlparse

WEAK_FORUMS = ("reddit.", "quora.", "stackexchange.", "stackoverflow.", "forum", "community")
THIN_PATTERNS = ("what is", "definition", "quick guide", "short guide")
OLD_YEAR_RE = re.compile(r"\b(201[0-9]|2020|2021)\b")

def _domain(url: str) -> str:
    try:
        d = urlparse(url).netloc.lower()
        return d.removeprefix("www.")
    except Exception:
        return url

def _assess(r: Dict[str, Any]) -> Dict[str, Any]:
    title = (r.get("title") or "").lower()
    snippet = (r.get("snippet") or r.get("description") or "").lower()
    url = r.get("url") or r.get("link") or ""
    d = _domain(url)

    is_forum = any(s in d or s in title for s in WEAK_FORUMS)
    is_thin  = any(p in title for p in THIN_PATTERNS) or len(snippet) < 80
    is_old   = bool(OLD_YEAR_RE.search(snippet))
    weak     = is_forum or is_thin or is_old

    return {**r,
            "domain": d,
            "weak_forum": is_forum,
            "weak_thin": is_thin,
            "weak_old": is_old,
            "weak_any": weak}

def analyze_serp(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [_assess(r) for r in (results or [])][:5]
    summary = {
        "total": len(rows),
        "weak_any": sum(r["weak_any"]  for r in rows),
        "weak_forum": sum(r["weak_forum"] for r in rows),
        "weak_thin": sum(r["weak_thin"]  for r in rows),
        "weak_old":  sum(r["weak_old"]   for r in rows),
    }
    return {"rows": rows, "summary": summary}
