# eval_logger.py
import json, os, uuid, datetime
from typing import Any, Dict, Optional

LOG_DIR = "data"
LOG_PATH = os.path.join(LOG_DIR, "evals.jsonl")

def _ensure_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

def log_eval(
    *,
    variant: str,
    keyword: str,
    prompt: str,
    output: str,
    latency_ms: float,
    tokens_prompt: Optional[int] = None,
    tokens_completion: Optional[int] = None,
    user_rating: Optional[int] = None,   # 1–5
    user_notes: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """Append a single evaluation row to JSONL."""
    _ensure_dir()
    # Use timezone-aware UTC timestamp (avoid deprecated utcnow)
    ts = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    row = {
        "id": str(uuid.uuid4()),
        "ts": ts,
        "variant": variant,
        "keyword": keyword,
        "prompt": prompt,
        "latency_ms": round(latency_ms, 1),
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "user_rating": user_rating,
        "user_notes": user_notes,
        "output_chars": len(output) if output else 0,
        "extra": extra or {},
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
