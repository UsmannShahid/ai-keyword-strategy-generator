# parsing.py
"""
Robust parsing utilities for keyword extraction from LLM responses.
Handles various response formats including JSON, prose, and malformed responses.
"""

from __future__ import annotations
import json
import re
from typing import Dict, Any, List, Tuple

# Safe fallback output structure
SAFE_OUTPUT = {
    "informational": [],
    "transactional": [],
    "branded": []
}

def parse_keywords_from_model(raw_text: str) -> Dict[str, Any]:
    """
    Parse keywords from model response with robust fallback handling.
    
    Tries multiple parsing strategies:
    1. Direct JSON parsing
    2. Extract JSON from code blocks (```json or ```)
    3. Extract JSON object from prose
    4. Fallback to safe empty structure
    
    Args:
        raw_text: Raw response text from the LLM
        
    Returns:
        Dict with keys: informational, transactional, branded
        Each containing a list of keyword strings
    """
    if not raw_text or not isinstance(raw_text, str):
        return SAFE_OUTPUT.copy()
    
    # Strategy 1: Direct JSON parsing
    try:
        result = json.loads(raw_text.strip())
        if _is_valid_keyword_structure(result):
            return result
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from code blocks
    result = _extract_from_code_blocks(raw_text)
    if result:
        return result
    
    # Strategy 3: Extract JSON object from prose
    result = _extract_json_from_prose(raw_text)
    if result:
        return result
    
    # Strategy 4: Try to parse as simple list format
    result = _parse_simple_list_format(raw_text)
    if result:
        return result
    
    # Final fallback: return safe empty structure
    return SAFE_OUTPUT.copy()

def _is_valid_keyword_structure(data: Any) -> bool:
    """Check if parsed data has the expected keyword structure."""
    if not isinstance(data, dict):
        return False
    
    expected_keys = {"informational", "transactional", "branded"}
    data_keys = set(data.keys())
    
    # Must have at least one expected key
    if not (data_keys & expected_keys):
        return False
    
    # All values should be lists
    for key in data_keys & expected_keys:
        if not isinstance(data[key], list):
            return False
    
    return True

def _extract_from_code_blocks(text: str) -> Dict[str, Any] | None:
    """Extract JSON from markdown code blocks."""
    patterns = [
        r'```(?:json)?\s*(\{.*?\})\s*```',  # ```json or ```
        r'`(\{.*?\})`',                      # Single backticks
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                result = json.loads(match.group(1))
                if _is_valid_keyword_structure(result):
                    return result
            except json.JSONDecodeError:
                continue
    
    return None

def _extract_json_from_prose(text: str) -> Dict[str, Any] | None:
    """Extract JSON object from prose text."""
    # Look for JSON-like structures
    patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Nested JSON
        r'\{[^}]+\}',                         # Simple JSON
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.DOTALL)
        for match in matches:
            try:
                result = json.loads(match.group(0))
                if _is_valid_keyword_structure(result):
                    return result
            except json.JSONDecodeError:
                continue
    
    return None

def _parse_simple_list_format(text: str) -> Dict[str, Any] | None:
    """
    Parse simple list formats like:
    Informational: keyword1, keyword2
    Transactional: keyword3, keyword4
    """
    result = SAFE_OUTPUT.copy()
    found_any = False
    
    # Pattern to match category headers and keywords
    patterns = {
        "informational": [
            r"informational[:\s]+([^\n]+)",
            r"information[:\s]+([^\n]+)",
            r"info[:\s]+([^\n]+)",
        ],
        "transactional": [
            r"transactional[:\s]+([^\n]+)",
            r"transaction[:\s]+([^\n]+)",
            r"commercial[:\s]+([^\n]+)",
        ],
        "branded": [
            r"branded[:\s]+([^\n]+)",
            r"brand[:\s]+([^\n]+)",
        ]
    }
    
    for category, category_patterns in patterns.items():
        for pattern in category_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                keywords_text = match.group(1).strip()
                # Split by common delimiters
                keywords = [
                    kw.strip().strip('"\'`') 
                    for kw in re.split(r'[,;|•\n]', keywords_text)
                    if kw.strip()
                ]
                if keywords:
                    result[category].extend(keywords)
                    found_any = True
    
    return result if found_any else None

def clean_keywords(keywords_dict: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Clean and validate keyword dictionary.
    
    Args:
        keywords_dict: Raw keywords dictionary
        
    Returns:
        Cleaned dictionary with guaranteed structure
    """
    result = SAFE_OUTPUT.copy()
    
    for category in ["informational", "transactional", "branded"]:
        if category in keywords_dict:
            raw_keywords = keywords_dict[category]
            if isinstance(raw_keywords, list):
                # Clean each keyword
                cleaned = []
                for kw in raw_keywords:
                    if isinstance(kw, str):
                        clean_kw = kw.strip().strip('"\'`')
                        if clean_kw and len(clean_kw) > 1:  # Skip very short keywords
                            cleaned.append(clean_kw)
                result[category] = cleaned
    
    return result

def validate_keywords_response(data: Any) -> Dict[str, List[str]]:
    """
    Validate and clean a keywords response from any source.
    
    Args:
        data: Response data (could be dict, string, or other)
        
    Returns:
        Valid keywords dictionary
    """
    if isinstance(data, str):
        parsed = parse_keywords_from_model(data)
    elif isinstance(data, dict):
        parsed = data
    else:
        parsed = SAFE_OUTPUT.copy()
    
    return clean_keywords(parsed)

# =========================
# Brief parsing helpers
# =========================

def parse_brief_output(raw: str) -> Tuple[Dict[str, Any], bool]:
    """
    Try to parse LLM output for content briefs as JSON.
    Returns (data, is_json). If not JSON, returns ({'raw': raw}, False).
    Accepts plain JSON or JSON inside Markdown code fences.
    """
    raw = (raw or "").strip()
    if not raw:
        return {"raw": ""}, False

    # 1) Direct JSON
    try:
        return json.loads(raw), True
    except Exception:
        pass

    # 2) JSON in code fences (``` ... ```), possibly with ```json
    if raw.startswith("```"):
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = raw[start:end+1]
            try:
                return json.loads(snippet), True
            except Exception:
                pass

    # 3) Last-resort: try to pull the biggest {...} block
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start:end+1]
        try:
            return json.loads(snippet), True
        except Exception:
            pass

    # Fallback to raw text
    return {"raw": raw}, False


def detect_placeholders(brief: Dict[str, Any]) -> bool:
    """
    Heuristic to flag generic placeholders in a brief
    (e.g., 'Chair Name #1', 'Product #1', etc.).
    """
    try:
        text = json.dumps(brief, ensure_ascii=False).lower()
    except Exception:
        text = str(brief).lower()

    patterns = [
        "name #1", "name #2",
        "product #1", "product #2",
        "chair name #1", "model #1",
        "example #1", "h3 1", "h2 1"
    ]
    return any(p in text for p in patterns)

# ---------- Generic JSON parser for tool outputs ----------
from typing import Tuple

def parse_json_object(raw: str) -> Tuple[Dict[str, Any], bool]:
    """
    Parse a single JSON object from raw text (direct or inside code fences).
    Returns (data, is_json). If parsing fails, returns ({"raw": raw}, False).
    """
    if not isinstance(raw, str):
        return {"raw": str(raw)}, False
    txt = raw.strip()
    if not txt:
        return {"raw": ""}, False

    # 1) direct
    try:
        return json.loads(txt), True
    except Exception:
        pass

    # 2) code fence or mixed text -> extract largest {...}
    start = txt.find("{")
    end = txt.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = txt[start:end+1]
        try:
            return json.loads(snippet), True
        except Exception:
            pass

    return {"raw": txt}, False