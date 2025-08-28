"""
Google Keyword Planner (GKP) data loader and filter functions.
Handles loading, filtering, and processing of keyword data based on user topics and plans.
"""

import pandas as pd
import os
from typing import List, Dict, Any, Optional


def load_gkp_keywords(topic: str, max_results: int = 20, plan_settings: dict = None) -> List[Dict[str, Any]]:
    """
    Load and filter GKP keyword data based on user topic.
    
    Args:
        topic: User input topic to filter keywords
        max_results: Maximum number of results to return
        plan_settings: User plan settings for additional filtering/features
    
    Returns:
        List of keyword dictionaries with search volume, competition, and CPC data
    """
    # Path to GKP data file
    csv_path = os.path.join("data", "gkp_keywords.csv")
    
    try:
        # Load the CSV data
        df = pd.read_csv(csv_path)
        
        # Standardize column names (handle potential variations)
        df.columns = df.columns.str.strip()
        if 'Keyword' not in df.columns:
            # Try common alternatives
            for col in ['keyword', 'Keywords', 'KEYWORD']:
                if col in df.columns:
                    df = df.rename(columns={col: 'Keyword'})
                    break
        
        # Convert to lowercase for filtering
        df['Keyword_lower'] = df['Keyword'].str.lower()
        topic_lower = topic.lower().strip()
        
        # Filter keywords that contain the topic
        if topic_lower:
            # Use multiple filtering strategies for better results
            filters = [
                df['Keyword_lower'].str.contains(topic_lower, na=False),
                df['Keyword_lower'].str.contains(topic_lower.replace(' ', ''), na=False),  # Handle spacing
            ]
            
            # Try splitting topic into words for broader matching
            topic_words = topic_lower.split()
            if len(topic_words) > 1:
                for word in topic_words:
                    if len(word) > 2:  # Only meaningful words
                        filters.append(df['Keyword_lower'].str.contains(word, na=False))
            
            # Combine filters with OR logic
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter | f
                
            filtered_df = df[combined_filter]
        else:
            # No topic provided, return top keywords
            filtered_df = df
        
        # Sort by search volume (descending)
        if 'Search Volume' in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by='Search Volume', ascending=False)
        
        # Apply plan-specific limits
        if plan_settings:
            max_results = min(max_results, plan_settings.get("max_keywords", max_results))
        
        # Take top results
        result_df = filtered_df.head(max_results)
        
        # Convert to list of dictionaries, excluding the helper column
        result_df = result_df.drop(columns=['Keyword_lower'], errors='ignore')
        keywords = result_df.to_dict('records')
        
        # Add metadata
        for kw in keywords:
            kw['source'] = 'Google Keyword Planner'
            kw['filtered_by'] = topic if topic else 'No filter'
        
        return keywords
        
    except FileNotFoundError:
        print(f"Warning: GKP keyword file not found at {csv_path}")
        return _get_fallback_keywords(topic, max_results)
    
    except Exception as e:
        print(f"Error loading GKP keywords: {str(e)}")
        return _get_fallback_keywords(topic, max_results)


def _get_fallback_keywords(topic: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Fallback keywords when CSV is not available.
    
    Args:
        topic: User topic
        max_results: Maximum results to return
        
    Returns:
        List of mock keyword data
    """
    base_keywords = [
        {"Keyword": f"best {topic}", "Search Volume": 5400, "Competition": 0.3, "CPC": 1.25},
        {"Keyword": f"{topic} guide", "Search Volume": 3200, "Competition": 0.25, "CPC": 0.95},
        {"Keyword": f"how to choose {topic}", "Search Volume": 2800, "Competition": 0.2, "CPC": 0.85},
        {"Keyword": f"{topic} reviews", "Search Volume": 4100, "Competition": 0.35, "CPC": 1.15},
        {"Keyword": f"affordable {topic}", "Search Volume": 1900, "Competition": 0.15, "CPC": 0.65},
        {"Keyword": f"professional {topic}", "Search Volume": 2100, "Competition": 0.45, "CPC": 1.75},
        {"Keyword": f"{topic} for beginners", "Search Volume": 1600, "Competition": 0.2, "CPC": 0.75},
        {"Keyword": f"{topic} comparison", "Search Volume": 1800, "Competition": 0.3, "CPC": 1.05},
        {"Keyword": f"top {topic}", "Search Volume": 2600, "Competition": 0.4, "CPC": 1.35},
        {"Keyword": f"{topic} tips", "Search Volume": 1400, "Competition": 0.25, "CPC": 0.85},
    ]
    
    # Add metadata
    for kw in base_keywords:
        kw['source'] = 'Fallback data'
        kw['filtered_by'] = topic
    
    return base_keywords[:max_results]


def get_keyword_stats(keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics from keyword list.
    
    Args:
        keywords: List of keyword dictionaries
        
    Returns:
        Dictionary with statistics
    """
    if not keywords:
        return {
            "total_keywords": 0,
            "avg_volume": 0,
            "avg_competition": 0,
            "avg_cpc": 0,
            "total_volume": 0
        }
    
    try:
        volumes = [kw.get('Search Volume', 0) for kw in keywords if isinstance(kw.get('Search Volume'), (int, float))]
        competitions = [kw.get('Competition', 0) for kw in keywords if isinstance(kw.get('Competition'), (int, float))]
        cpcs = [kw.get('CPC', 0) for kw in keywords if isinstance(kw.get('CPC'), (int, float))]
        
        return {
            "total_keywords": len(keywords),
            "avg_volume": round(sum(volumes) / len(volumes), 0) if volumes else 0,
            "avg_competition": round(sum(competitions) / len(competitions), 2) if competitions else 0,
            "avg_cpc": round(sum(cpcs) / len(cpcs), 2) if cpcs else 0,
            "total_volume": sum(volumes),
            "high_volume_count": len([v for v in volumes if v > 3000]),
            "low_competition_count": len([c for c in competitions if c < 0.3])
        }
    except Exception as e:
        print(f"Error calculating keyword stats: {str(e)}")
        return {"total_keywords": len(keywords), "error": str(e)}


def format_keyword_for_display(keyword: Dict[str, Any]) -> str:
    """
    Format a keyword dictionary for nice display.
    
    Args:
        keyword: Keyword dictionary
        
    Returns:
        Formatted string for display
    """
    kw_name = keyword.get('Keyword', 'Unknown')
    volume = keyword.get('Search Volume', 0)
    competition = keyword.get('Competition', 0)
    cpc = keyword.get('CPC', 0)
    
    # Format volume with commas
    volume_str = f"{volume:,}" if isinstance(volume, (int, float)) else str(volume)
    
    # Format competition as percentage
    comp_str = f"{competition:.0%}" if isinstance(competition, (int, float)) else str(competition)
    
    # Format CPC as currency
    cpc_str = f"${cpc:.2f}" if isinstance(cpc, (int, float)) else str(cpc)
    
    return f"**{kw_name}** — Volume: {volume_str} | Competition: {comp_str} | CPC: {cpc_str}"
