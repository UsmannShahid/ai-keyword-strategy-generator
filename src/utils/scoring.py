"""
Scoring utilities for keyword analysis.
"""

import pandas as pd
from typing import Dict, Any

def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add scoring columns to the keyword dataframe."""
    if df.empty:
        return df
    
    df = df.copy()
    
    # If keywords already have scores (from new API), keep them
    if 'quick_win_score' in df.columns:
        return df
    
    # Otherwise add mock scores for backwards compatibility
    df['quick_win_score'] = 75
    df['search_volume'] = 1000
    df['difficulty'] = 'Medium'
    
    return df

def quickwin_breakdown(score: float) -> Dict[str, Any]:
    """Break down a quick win score into components."""
    return {
        "overall_score": score,
        "volume_score": 80,
        "competition_score": 70,
        "relevance_score": 75
    }

def explain_quickwin(score: float) -> str:
    """Explain what a quick win score means."""
    if score >= 80:
        return "Excellent opportunity - high volume, low competition"
    elif score >= 60:
        return "Good opportunity - balanced volume and competition"
    elif score >= 40:
        return "Moderate opportunity - some challenges present"
    else:
        return "Challenging opportunity - high competition or low volume"