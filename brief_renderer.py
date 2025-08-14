# brief_renderer.py
"""
Render a content brief dict (parsed from the LLM) into clean, writer-friendly Markdown.
Usage:
    from brief_renderer import brief_to_markdown
    md = brief_to_markdown(brief_dict)
"""

from __future__ import annotations
from typing import Any, Dict, Iterable, List


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _outline_lines(brief: Dict[str, Any]) -> List[str]:
    """
    Supports shapes like:
    outline = {"H2": ["Intro", {"H3": ["a","b"]}, "Conclusion"]}
    """
    lines: List[str] = []
    outline = brief.get("outline") or {}
    h2s = outline.get("H2") or outline.get("h2") or []
    if not isinstance(h2s, list):
        return lines

    idx = 1
    for item in h2s:
        if isinstance(item, str):
            lines.append(f"{idx}. **{item}**")
            idx += 1
        elif isinstance(item, dict):
            h3s = item.get("H3") or item.get("h3") or []
            for h3 in _as_list(h3s):
                lines.append(f"   - {h3}")
        else:
            lines.append(f"- {item}")
    return lines


def _bullets(title: str, items: Iterable[str]) -> str:
    items = [str(x).strip() for x in items if str(x).strip()]
    if not items:
        return ""
    bullets = "\n".join(f"- {x}" for x in items)
    return f"## {title}\n{bullets}\n"


def brief_to_markdown(brief: Dict[str, Any]) -> str:
    """
    Convert a normalized brief dict to modern Markdown.
    Expected keys (best effort): title, meta_description, outline, related_keywords,
    suggested_word_count, content_type, internal_link_ideas, external_link_ideas, faqs.
    """
    title = brief.get("title") or ""
    meta = brief.get("meta_description") or brief.get("meta") or ""
    related = _as_list(brief.get("related_keywords") or brief.get("entities"))
    wc = brief.get("suggested_word_count")
    ctype = brief.get("content_type")
    internal = _as_list(brief.get("internal_link_ideas"))
    external = _as_list(brief.get("external_link_ideas"))
    faqs = brief.get("faqs") or []

    parts: List[str] = []

    if title:
        parts.append(f"## 📝 Title\n{title}\n")
    if meta:
        parts.append(f"## 🧾 Meta Description\n{meta}\n")

    outline_md = "\n".join(_outline_lines(brief))
    if outline_md.strip():
        parts.append(f"## 📚 Outline\n{outline_md}\n")

    specs = []
    if wc:
        specs.append(f"- Suggested Word Count: **{wc}**")
    if ctype:
        specs.append(f"- Content Type: **{ctype}**")
    if specs:
        parts.append("## 📏 Specs\n" + "\n".join(specs) + "\n")

    if related:
        parts.append(_bullets("🔑 Related Keywords", related))

    if internal:
        parts.append(_bullets("🔗 Internal Link Ideas", internal))

    if external:
        ext_fmt = []
        for x in external:
            if isinstance(x, str) and x.startswith("http"):
                ext_fmt.append(f"[{x}]({x})")
            else:
                ext_fmt.append(str(x))
        parts.append(_bullets("🌐 External Link Ideas", ext_fmt))

    if faqs:
        faq_lines = []
        for f in faqs:
            if isinstance(f, dict):
                q = (f.get("question") or "").strip()
                a = (f.get("answer") or "").strip()
                if q and a:
                    faq_lines.append(f"**Q:** {q}\n**A:** {a}")
            else:
                faq_lines.append(f"- {f}")
        if faq_lines:
            parts.append("## ❓ FAQs\n" + "\n\n".join(faq_lines) + "\n")

    parts.append("> ✅ Tip: Add 1–2 internal CTAs and a comparison table if buyer intent is strong.\n")
    return "\n".join(parts).strip()
