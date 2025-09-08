# api/services/quick_wins.py
import pandas as pd
from typing import List, Dict, Tuple

# Define progressive tiers for what constitutes a "Quick Win"
# Tier 1: Ideal (very low competition, good volume)
# Tier 2: Good (low competition, any volume)
# Tier 3: Decent (moderate competition, good volume)
# Tier 4: Best Available (lowest competition score, regardless of volume)
QUICK_WIN_TIERS = [
    {"name": "Ideal", "max_comp": 0.30, "min_vol": 1000},
    {"name": "Good", "max_comp": 0.40, "min_vol": 100},
    {"name": "Decent", "max_comp": 0.50, "min_vol": 500},
    {"name": "Best Available", "max_comp": 1.0, "min_vol": 0}, # Fallback tier
]

def compute_quick_wins_always(
    keyword_items: List[Dict], want: int = 10
) -> Tuple[List[Dict], Dict]:
    """
    Finds Quick Win keywords using a progressive fallback strategy.
    
    Returns a tuple of (quick_wins_list, metadata_dict).
    """
    if not keyword_items:
        return [], {"tier": "none", "candidates": 0, "error": "No keyword items provided."}

    df = pd.DataFrame(keyword_items)
    
    # Ensure required columns exist
    if "competition" not in df.columns or "volume" not in df.columns:
        return [], {"tier": "none", "candidates": len(df), "error": "Missing 'competition' or 'volume' data."}

    # --- Progressive Fallback Logic ---
    for i, tier in enumerate(QUICK_WIN_TIERS):
        tier_name = tier["name"]
        max_comp = tier["max_comp"]
        min_vol = tier["min_vol"]
        
        # Filter candidates based on the current tier's criteria
        candidates = df[
            (df["competition"] <= max_comp) & (df["volume"] >= min_vol)
        ].copy()
        
        print(f"DEBUG: Trying Tier '{tier_name}'. Found {len(candidates)} candidates.")

        if not candidates.empty:
            # If we found candidates, calculate score and return the best ones
            # Score = (Volume / Competition) - higher is better. Add 0.01 to avoid division by zero.
            candidates["opportunity_score"] = candidates["volume"] / (candidates["competition"] + 0.01)
            
            # Sort by the highest opportunity score
            top_wins = candidates.sort_values(by="opportunity_score", ascending=False).head(want)
            
            meta = {
                "tier_used": tier_name,
                "candidates_found": len(candidates),
                "total_pool_size": len(df),
            }
            return top_wins.to_dict("records"), meta

    # If no tiers found any results (very unlikely with the fallback), return an empty list
    meta = {
        "tier_used": "none",
        "total_pool_size": len(df),
        "error": "No keywords matched even the most lenient criteria.",
    }
    return [], meta