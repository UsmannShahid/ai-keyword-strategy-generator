# tests/test_services.py
import json
import services
import llm_client

def test_wrapped_json_parses(monkeypatch):
    def fake(_): 
        return "Here:\n" + json.dumps({"informational":["k1"],"transactional":[],"branded":[]}) + "\nThanks"
    monkeypatch.setattr(llm_client, "get_keywords_text", fake)
    out = services.get_keywords_safe("x")
    assert out["informational"] == ["k1"]

def test_garbage_uses_safe_shape(monkeypatch):
    monkeypatch.setattr(llm_client, "get_keywords_text", lambda _: "totally not json")
    out = services.get_keywords_safe("x")
    assert all(k in out for k in ("informational","transactional","branded"))
