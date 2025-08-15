# serp_utils.py
from __future__ import annotations
from typing import List, Dict, Any
import re
from urllib.parse import urlparse

WEAK_FORUMS = ("reddit.", "quora.", "stackexchange.", "stack overflow", "forum", "community")
THIN_PATTERNS = ("what is", "definition", "short guide", "quick guide")
OLD_YEAR_RE = re.compile(r"\b(201[0-9]|2020|2021)\b")

def domain(root_url: str) -> str:
    try:
        netloc = urlparse(root_url).netloc.lower()
        return netloc.removeprefix("www.")
    except Exception:
        return root_url

def assess_result(r: Dict[str, Any]) -> Dict[str, Any]:
    """Add simple weakness signals to a SERP result dict."""
    title = (r.get("title") or "").lower()
    snippet = (r.get("snippet") or r.get("description") or "").lower()
    url = r.get("url") or r.get("link") or ""

    d = domain(url)
    is_forum = any(s in d or s in title for s in WEAK_FORUMS)
    is_thin = any(p in title for p in THIN_PATTERNS) or len(snippet) < 80
    is_old = bool(OLD_YEAR_RE.search(snippet))
    weak = is_forum or is_thin or is_old

    return {
        **r,
        "domain": d,
        "weak_forum": is_forum,
        "weak_thin": is_thin,
        "weak_old": is_old,
        "weak_any": weak,
    }

def analyze_serp(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = [assess_result(r) for r in (results or [])][:5]
    summary = {
        "total": len(rows),
        "weak_any": sum(1 for r in rows if r["weak_any"]),
        "weak_forum": sum(1 for r in rows if r["weak_forum"]),
        "weak_thin": sum(1 for r in rows if r["weak_thin"]),
        "weak_old": sum(1 for r in rows if r["weak_old"]),
    }
    return {"rows": rows, "summary": summary}
