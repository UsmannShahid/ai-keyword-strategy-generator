# api/core/keywords.py
import pandas as pd
from pathlib import Path

GKP_PATH = Path("data/gkp_keywords.csv")

def load_gkp_keywords(topic: str, limit: int = 20):
    if not GKP_PATH.exists():
        return []
    df = pd.read_csv(GKP_PATH)
    df["Keyword"] = df["Keyword"].astype(str).str.lower()
    filtered = df[df["Keyword"].str.contains(topic.lower(), na=False)]
    filtered = filtered.sort_values(by="Search Volume", ascending=False)
    rows = filtered.head(limit)
    out = []
    for _, r in rows.iterrows():
        out.append({
            "keyword": r.get("Keyword"),
            "volume": int(r.get("Search Volume", 0)) if pd.notna(r.get("Search Volume")) else None,
            "cpc": float(r.get("CPC", 0)) if pd.notna(r.get("CPC")) else None,
            "competition": float(r.get("Competition", 0)) if pd.notna(r.get("Competition")) else None,
            "source": "GKP",
        })
    return out
