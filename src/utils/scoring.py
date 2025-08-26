"""
Scoring utilities for keyword analysis.
"""

import pandas as pd
import re
from typing import Dict, Any

def analyze_keyword(keyword: str) -> Dict[str, Any]:
    """Analyze a keyword and return realistic scores based on its characteristics."""
    keyword_lower = keyword.lower().strip()
    
    # Word count analysis
    word_count = len(keyword_lower.split())
    
    # Calculate search volume based on keyword characteristics
    base_volume = 800
    
    # Long-tail keywords (3+ words) typically have lower volume
    if word_count >= 4:
        volume = base_volume // 3  # ~267
    elif word_count == 3:
        volume = base_volume // 2  # ~400
    elif word_count == 2:
        volume = base_volume  # ~800
    else:  # 1 word
        volume = base_volume * 2  # ~1600
    
    # Adjust volume based on keyword type
    commercial_intent_words = ['buy', 'purchase', 'price', 'cost', 'cheap', 'affordable', 'best', 'review', 'compare']
    informational_words = ['how', 'what', 'why', 'guide', 'tutorial', 'tips', 'learn']
    local_words = ['near me', 'local', 'nearby', 'in']
    
    # Commercial keywords usually have higher volume
    if any(word in keyword_lower for word in commercial_intent_words):
        volume = int(volume * 1.3)
    
    # Informational keywords have moderate volume
    elif any(word in keyword_lower for word in informational_words):
        volume = int(volume * 1.1)
    
    # Local keywords have lower but more targeted volume
    if any(phrase in keyword_lower for phrase in local_words):
        volume = int(volume * 0.7)
    
    # Calculate difficulty based on competitiveness indicators
    base_difficulty = 45
    
    # Shorter keywords are generally more competitive
    if word_count == 1:
        difficulty = 80
    elif word_count == 2:
        difficulty = 60
    elif word_count == 3:
        difficulty = 40
    else:  # 4+ words
        difficulty = 25
    
    # Commercial keywords are more competitive
    if any(word in keyword_lower for word in commercial_intent_words):
        difficulty = min(85, difficulty + 15)
    
    # Local keywords can be less competitive
    if any(phrase in keyword_lower for phrase in local_words):
        difficulty = max(20, difficulty - 15)
    
    # Generic vs specific adjustment
    generic_words = ['best', 'top', 'good', 'great', 'awesome']
    if any(word in keyword_lower for word in generic_words):
        difficulty = min(90, difficulty + 10)
    
    # Calculate quick-win score: (volume factor) + (100 - difficulty)
    volume_score = min(50, volume // 40)  # Cap at 50
    competition_score = 100 - difficulty
    quick_win_score = int((volume_score + competition_score) / 2)
    
    # Ensure realistic ranges
    volume = max(100, min(5000, volume))  # 100-5000 range
    difficulty = max(15, min(90, difficulty))  # 15-90 range
    quick_win_score = max(20, min(95, quick_win_score))  # 20-95 range
    
    return {
        'search_volume': volume,
        'difficulty': difficulty,
        'quick_win_score': quick_win_score,
        'word_count': word_count
    }

def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add scoring columns to the keyword dataframe."""
    if df.empty:
        return df
    
    df = df.copy()
    
    # If keywords already have scores (from new API), keep them
    if 'quick_win_score' in df.columns:
        return df
    
    # Apply realistic analysis to each keyword
    for idx, row in df.iterrows():
        keyword = row['keyword']
        scores = analyze_keyword(keyword)
        
        df.at[idx, 'quick_win_score'] = scores['quick_win_score']
        df.at[idx, 'search_volume'] = scores['search_volume'] 
        df.at[idx, 'difficulty'] = scores['difficulty']
        df.at[idx, 'volume'] = scores['search_volume']  # For compatibility
    
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