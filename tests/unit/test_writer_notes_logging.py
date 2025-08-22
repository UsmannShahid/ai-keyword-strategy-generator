import json, os, tempfile, importlib

def test_writer_notes_logging(monkeypatch):
    import eval_logger as el
    tmp = tempfile.mkdtemp()
    el.LOG_DIR = tmp
    el.LOG_PATH = os.path.join(tmp, "evals.jsonl")
    importlib.reload(el)

    el.log_eval(
        variant="B",
        keyword="test",
        prompt="p",
        output=json.dumps({"writer_notes":["x"]}),
        latency_ms=0,
        extra={"type":"writer_notes","writer_notes_style_label":"Detailed","writer_notes_variant":"B"}
    )

    assert os.path.exists(el.LOG_PATH)
    row = json.loads(open(el.LOG_PATH, encoding="utf-8").read().splitlines()[-1])

    assert row["variant"] == "B"
    assert row["extra"]["writer_notes_style_label"] == "Detailed"
    assert row["extra"]["writer_notes_variant"] == "B"
