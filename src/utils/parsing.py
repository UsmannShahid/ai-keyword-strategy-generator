"""
Parsing utilities for keyword generation.
"""

import json
from typing import Dict, Any, List, Tuple

SAFE_OUTPUT = {
    "informational": ["example informational keyword"],
    "transactional": ["example transactional keyword"], 
    "branded": ["example branded keyword"]
}

def parse_brief_output(text: str) -> Tuple[Dict[str, Any], bool]:
    """Parse brief output text into structured format."""
    try:
        # Try to parse as JSON first
        data = json.loads(text)
        return data, True
    except:
        # Fallback to treating as plain text
        return {"content": text}, False

def detect_placeholders(text: str) -> List[str]:
    """Detect placeholder text in content."""
    placeholders = []
    if "[" in text and "]" in text:
        import re
        placeholders = re.findall(r'\[([^\]]+)\]', text)
    return placeholders

def parse_json_object(text: str) -> Tuple[Dict[str, Any], bool]:
    """Parse JSON object from text."""
    try:
        data = json.loads(text.strip())
        return data, True
    except:
        return {}, False