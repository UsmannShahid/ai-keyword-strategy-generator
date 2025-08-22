import json
import pytest

# monkeypatch llm to avoid API calls
def test_generate_writer_notes_parses(monkeypatch):
    from services import generate_writer_notes

    sample_out = json.dumps({
        "target_audience": "remote workers",
        "search_intent": "transactional",
        "primary_angle": "ergonomics + budget",
        "writer_notes": ["Lead with posture pain points", "Compare mesh vs. foam support"],
        "must_cover_sections": ["Pros/Cons of top archetypes", "Sizing & fit guide"],
        "entity_gaps": ["adjustable lumbar", "BIFMA standards"],
        "data_freshness": ["Update 2025 studies on back pain"],
        "internal_link_targets": ["/home-office-setup", "/chair-size-guide"],
        "external_citations_needed": ["NIOSH ergonomics guidance"],
        "formatting_enhancements": ["comparison table", "checklist", "schema:FAQPage"],
        "tone_style": ["expert","friendly","second-person"],
        "cta_ideas": ["See our setup checklist"],
        "risk_flags": [],
        "recommended_word_count": 1400
    })

    class FakeResp(dict):
        pass

    def fake_generate_text(prompt, json_mode=False):
        return {"text": sample_out, "usage": {"prompt_tokens": 100, "completion_tokens": 200}}

    monkeypatch.setenv("PYTHONHASHSEED", "0")
    # Patch the function in the services module where it's imported
    import services
    monkeypatch.setattr(services, "generate_text", fake_generate_text, raising=True)

    notes, ok, prompt, usage = generate_writer_notes(
        keyword="best ergonomic chair for home office",
        brief_dict={"outline":{"H2":["Intro"]}},
        serp_summary={"weak_any":2},
        variant="A",
    )

    assert ok is True
    assert isinstance(notes, dict)
    assert notes["search_intent"] in {"informational","transactional","local","navigational"}
    assert "writer_notes" in notes and isinstance(notes["writer_notes"], list)
    assert usage and "completion_tokens" in usage
