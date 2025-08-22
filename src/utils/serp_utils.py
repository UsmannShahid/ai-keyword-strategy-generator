"""
SERP analysis utilities.
"""

from typing import List, Dict, Any

def analyze_serp(serp_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze SERP data and return insights."""
    if not serp_data:
        return {"summary": "No SERP data available"}
    
    analysis = {
        "total_results": len(serp_data),
        "domains": list(set(result.get("url", "").split("/")[2] for result in serp_data if result.get("url"))),
        "avg_title_length": sum(len(result.get("title", "")) for result in serp_data) / len(serp_data),
        "summary": f"Analyzed {len(serp_data)} SERP results"
    }
    
    return analysis