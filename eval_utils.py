import json, os
import pandas as pd
from typing import Optional

LOG_DIR = "data"
LOG_PATH = os.path.join(LOG_DIR, "evals.jsonl")

def load_evals_df(path: Optional[str] = None) -> pd.DataFrame:
    path = path or LOG_PATH
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=[
            "id","ts","variant","keyword","latency_ms","user_rating",
            "tokens_prompt","tokens_completion","output_chars","extra"
        ])
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    df = pd.DataFrame(rows)
    # Ensure expected columns exist
    for col in ["variant","keyword","latency_ms","user_rating","output_chars","ts"]:
        if col not in df.columns: df[col] = None
    # Flatten a couple of fields from extra if present
    if "extra" in df.columns:
        df["auto_flags"] = df["extra"].apply(lambda x: (x or {}).get("auto_flags"))
        df["is_json"] = df["extra"].apply(lambda x: (x or {}).get("is_json"))
    # Sorting newest first
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False)
    return df
