# api/core/keywords.py
import pandas as pd
from pathlib import Path
import json
from typing import List, Dict
from api.core.config import get_settings
from api.core.gpt import _get_client  # reuse your OpenAI client

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


# GPT-powered analysis functions (paid only)
ANALYSIS_SYSTEM = (
    "You are an SEO strategist. You output STRICT JSON only—no prose."
)

def build_analysis_prompt(gkp_items: List[Dict]) -> str:
    # reduce payload size for the model
    rows = [
        {
            "keyword": i.get("keyword"),
            "volume": i.get("volume"),
            "cpc": i.get("cpc"),
            "competition": i.get("competition"),
        }
        for i in gkp_items
    ]
    return (
        "Given this keyword list with volume, CPC, and competition, "
        "1) cluster them by intent (informational/commercial/navigational), "
        "2) propose 3–5 Quick Win keywords (low competition, decent volume), "
        "and 3) briefly note any channel ideas.\n\n"
        "Return JSON with keys: clusters, quick_wins, notes.\n\n"
        f"keywords={json.dumps(rows, ensure_ascii=False)}"
    )

def analyze_keywords_with_gpt(gkp_items: List[Dict], model: str) -> Dict:
    prompt = build_analysis_prompt(gkp_items)
    client = _get_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"}  # enforce JSON
    )
    txt = resp.choices[0].message.content.strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        # Fallback: minimal payload if model misbehaves
        return {"clusters": [], "quick_wins": [], "notes": "Could not parse JSON"}
