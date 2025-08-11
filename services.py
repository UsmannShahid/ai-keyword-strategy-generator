# services.py
from __future__ import annotations
import json
from typing import Dict, Any, Union

# Safe fallback output structure
SAFE_OUTPUT = {
    "informational": [],
    "transactional": [],
    "branded": []
}

def parse_keywords_from_model(raw_text: str) -> dict:
    """
    Parse keywords from model response with fallback handling.
    Tries to extract JSON even if wrapped in prose or code blocks.
    """
    try:
        # First try direct JSON parsing
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from code blocks or prose
        import re
        
        # Look for JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for JSON object in the text
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Fallback: return empty structure
        return SAFE_OUTPUT.copy()

def get_keywords_safe(prompt: str) -> Dict[str, Any]:
    """
    Returns a dict with keys you expect for to_dataframe().
    Tolerates:
      - existing JSON dict return (v1.1 behavior)
      - string return with JSON + extra prose
      - invalid/malformed JSON (falls back to SAFE_OUTPUT)
    """
    # Import the function from app.py (where it's actually defined)
    try:
        from app import get_keywords_text
        
        # Get raw text response
        raw_response = get_keywords_text(prompt)
        
        # Parse with robust fallback
        return parse_keywords_from_model(raw_response)
        
    except Exception as e:
        print(f"Warning: Error in get_keywords_safe: {e}")
        # If anything fails, return safe shape
        return SAFE_OUTPUT.copy()
