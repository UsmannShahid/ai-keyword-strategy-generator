# brief_renderer.py
"""
Render a content brief dict (parsed from the LLM) into clean, writer-friendly Markdown.
Usage:
    from brief_renderer import brief_to_markdown
    md = brief_to_markdown(brief_dict)
"""

from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional



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


# --- Friendly, plain-English explainer from SERP + brief intent ---


def _plain_english_explainer(
    keyword: str,
    intent: str | None,
    serp_summary: Dict[str, Any] | None,
    writer_notes: Dict[str, Any] | None,
) -> str:
    """
    Build a short, encouraging explanation for non-SEO users:
      - Why this looks winnable
      - What to do next
    """
    kw = keyword or "your topic"
    s = serp_summary or {}
    weak_any = int(s.get("weak_any", 0) or 0)
    wf = int(s.get("weak_forum", 0) or 0)
    wt = int(s.get("weak_thin", 0) or 0)
    wo = int(s.get("weak_old", 0) or 0)

    # Headline sentence
    verdict_bits = []
    if weak_any >= 3:
        verdict_bits.append("Good news — several current results look weak.")
    elif weak_any >= 1:
        verdict_bits.append("Promising—there are a few weak spots on page 1.")
    else:
        verdict_bits.append("Competitive—but still doable with a stronger article.")

    intent_phrase = ""
    if intent:
        il = str(intent).lower()
        if "transact" in il or "buyer" in il:
            intent_phrase = "Searchers likely want to compare options or buy."
        elif "info" in il:
            intent_phrase = "Searchers want clear, helpful information."
        elif "navig" in il or "brand" in il:
            intent_phrase = "Searchers may be looking for a specific brand/page."

    reasons = []
    if wf: reasons.append(f"forums ({wf})")
    if wt: reasons.append(f"thin answers ({wt})")
    if wo: reasons.append(f"outdated info ({wo})")
    reasons_line = ""
    if reasons:
        reasons_line = "Weaknesses spotted: " + ", ".join(reasons) + "."

    # Next steps (pull from writer notes if available, otherwise sensible defaults)
    wn = writer_notes or {}
    next_steps: list[str] = []

    # prefer real writer_notes bullets if present
    for b in (wn.get("writer_notes") or []):
        if len(next_steps) >= 4: break
        b = str(b).strip()
        if b: next_steps.append(b)

    # if we didn't have enough, pad with generic but helpful steps
    if len(next_steps) < 3:
        if wt or wo:
            next_steps.append("Add fresh 2024–2025 stats and cite recent sources.")
        if wf or wt:
            next_steps.append("Give a complete section-by-section guide; avoid one-line answers.")
        if "transact" in (intent or "").lower() or "buyer" in (intent or "").lower():
            next_steps.append("Add a comparison table + pros/cons to support a decision.")
        else:
            next_steps.append("Include a clear checklist or step-by-step instructions.")
        next_steps.append("Answer 3–5 common FAQs at the end.")

    # Build markdown
    lines = []
    lines.append("## 🧭 What this means (plain English)")
    lines.append(f"{' '.join(verdict_bits)} {intent_phrase}".strip())
    if reasons_line:
        lines.append(reasons_line)
    lines.append("")
    lines.append("## ✅ Next steps for your writer")
    for step in next_steps[:5]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)

# --- Extended, writer-ready variant that can merge Writer Notes + SERP summary ---
def _notes_lines(notes: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    if not isinstance(notes, dict):
        return lines

    def _add(title: str, items: Iterable[str]):
        items = [str(x).strip() for x in (items or []) if str(x).strip()]
        if items:
            lines.append(f"## {title}")
            lines.extend([f"- {x}" for x in items])
            lines.append("")

    # header trio
    hdr_bits = []
    if notes.get("target_audience"): hdr_bits.append(f"**Audience:** {notes['target_audience']}")
    if notes.get("search_intent"):   hdr_bits.append(f"**Intent:** {notes['search_intent']}")
    if notes.get("primary_angle"):   hdr_bits.append(f"**Primary angle:** {notes['primary_angle']}")
    if hdr_bits:
        lines.append("## 🧠 Writer’s Notes — Overview")
        lines.append("  \n".join(hdr_bits))
        lines.append("")

    _add("🧠 Writer notes", notes.get("writer_notes"))
    _add("📌 Must-cover sections", notes.get("must_cover_sections"))
    _add("🧩 Entity gaps", notes.get("entity_gaps"))
    _add("🗞️ Data freshness", notes.get("data_freshness"))
    _add("🔗 Internal link targets", notes.get("internal_link_targets"))
    _add("🌐 External citations needed", notes.get("external_citations_needed"))
    _add("🧰 Formatting enhancements", notes.get("formatting_enhancements"))
    _add("🎙️ Tone & style", notes.get("tone_style"))
    _add("🎯 CTA ideas", notes.get("cta_ideas"))
    _add("⚠️ Risk flags", notes.get("risk_flags"))

    if notes.get("recommended_word_count"):
        lines.append(f"**Recommended word count:** {notes['recommended_word_count']}")
        lines.append("")
    return lines

def _serp_summary_lines(serp_summary: Dict[str, Any]) -> List[str]:
    if not isinstance(serp_summary, dict):
        return []
    s = serp_summary or {}
    bits = []
    bits.append(f"- Weak spots total: **{s.get('weak_any', 0)}**")
    bits.append(f"- Forums: **{s.get('weak_forum', 0)}**, Thin: **{s.get('weak_thin', 0)}**, Old: **{s.get('weak_old', 0)}**")
    return ["## 🔍 SERP Snapshot — Summary", *bits, ""]

def brief_to_markdown_full(
    brief: Dict[str, Any],
    *,
    writer_notes: Optional[Dict[str, Any]] = None,
    serp_summary: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build a single, writer-ready Markdown doc:
      - Title, Meta, Outline, Specs, Related, Links, FAQs (from brief)
      - Optional: SERP Snapshot summary
      - Optional: Writer’s Notes
      - New: Plain-English explanation + next steps (non-SEO users)
    """
    base_md = brief_to_markdown(brief)
    parts: List[str] = [base_md]

    # SERP summary (compact bullets)
    if serp_summary:
        parts.append("\n".join(_serp_summary_lines(serp_summary)))

    # Plain-English explainer (encouraging & actionable)
    kw = (brief.get("title") or "").strip() or (brief.get("seed_keyword") or "")
    intent = (brief.get("content_type") or brief.get("intent") or "")
    explainer = _plain_english_explainer(kw, intent, serp_summary, writer_notes)
    parts.append(explainer)

    # Writer's notes (rich section)
    if writer_notes:
        parts.append("\n".join(_notes_lines(writer_notes)))

    # Closing tip stays last
    return "\n\n".join([p for p in parts if p and p.strip()])


