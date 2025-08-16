import json
from typing import Dict, Any, Optional, Tuple
from prompt_manager import prompt_manager
from llm_client import generate_text  # adjust if named differently
from parsing import parse_json_object
# Service wrapper for Writer's Notes
def generate_writer_notes(
    *,
    keyword: str,
    brief_dict: Dict[str, Any],
    serp_summary: Optional[Dict[str, Any]] = None,
    variant: str = "A",
) -> Tuple[Dict[str, Any], bool, str, Optional[Dict[str, int]]]:
    """
    Generate structured Writer's Notes as JSON using prompt variants A/B.
    Returns: (notes_dict, is_json, prompt_used, usage_dict)
    """
    prompt = prompt_manager.format_prompt_variant(
        base_name="writer_notes",
        variant=variant,
        keyword=keyword,
        brief_json=json.dumps(brief_dict, ensure_ascii=False),
        serp_summary_json=json.dumps(serp_summary or {}, ensure_ascii=False),
    )

    # Prefer JSON mode for strict JSON output if your client supports it
    result = generate_text(prompt, json_mode=True)  # set json_mode in llm_client if available
    # Normalize
    if isinstance(result, dict):
        raw_text = result.get("text") or result.get("output") or ""
        usage = result.get("usage")
    else:
        raw_text, usage = str(result), None

    notes, ok = parse_json_object(raw_text)
    return notes, ok, prompt, usage
# services.py
"""
High-level service functions for keyword generation.
Coordinates between LLM client and parsing logic.
"""

import json
from typing import Dict, Any, Optional, Tuple
from prompt_manager import prompt_manager
from llm_client import generate_text  # adjust if named differently
from parsing import parse_json_object
import time
from typing import Dict, Any, Tuple, Optional
from llm_client import KeywordLLMClient
from parsing import parse_keywords_from_model, validate_keywords_response, SAFE_OUTPUT
import llm_client
from prompt_manager import prompt_manager

class KeywordService:
    """Service class for keyword generation operations."""
    
    def __init__(self, llm_client: KeywordLLMClient = None):
        """
        Initialize the keyword service.
        
        Args:
            llm_client: Optional LLM client instance. If None, creates default.
        """
        self.llm_client = llm_client or KeywordLLMClient.create_default()
    
    def generate_keywords(
        self, 
        business_desc: str, 
        industry: str = "", 
        audience: str = "", 
        location: str = "",
        prompt_template: str = "default_seo"
    ) -> Dict[str, Any]:
        """
        Generate and parse keywords for a business.
        
        Args:
            business_desc: Main business description
            industry: Industry context
            audience: Target audience
            location: Geographic location/market
            prompt_template: Name of the prompt template to use
            
        Returns:
            Parsed keywords dictionary with fallback handling
        """
        try:
            # Generate raw response with specified prompt template
            raw_response = self.llm_client.generate_keywords(
                business_desc, industry, audience, location, prompt_template
            )
            
            # Parse with robust fallback
            return validate_keywords_response(raw_response)
            
        except Exception as e:
            print(f"Warning: Error in keyword generation: {e}")
            return SAFE_OUTPUT.copy()
    
    def generate_content_brief(
        self,
        seed_keyword: str,
        variant: str = "A"
    ) -> str:
        """
        Generate content brief for a specific keyword using prompt variants.
        
        Args:
            seed_keyword: The keyword to generate content brief for
            variant: Prompt variant to use ('A' or 'B')
            
        Returns:
            Generated content brief text
        """
        try:
            # Choose a variant from UI or config: 'A' or 'B'
            variant = variant  # e.g., from a Streamlit selectbox

            prompt = prompt_manager.format_prompt_variant(
                base_name="content_brief",
                variant=variant,
                keyword=seed_keyword,  # your variable
            )
            # send `prompt` to llm_client.generate(...) with JSON mode for structured output
            return self.llm_client.generate_content_brief(prompt)
            
        except Exception as e:
            print(f"Warning: Error in content brief generation: {e}")
            return f"Error generating content brief for '{seed_keyword}': {e}"
    
    def test_service(self) -> bool:
        """
        Test the entire service pipeline.
        
        Returns:
            True if service is working, False otherwise
        """
        try:
            # Test LLM connection
            if not self.llm_client.test_connection():
                return False
            
            # Test with simple input
            result = self.generate_keywords("online bookstore")
            
            # Check if we got valid structure
            return isinstance(result, dict) and "informational" in result
            
        except Exception:
            return False

# Legacy function for backward compatibility
def get_keywords_safe(prompt: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    
    Args:
        prompt: Raw prompt string
        
    Returns:
        Parsed keywords dictionary
    """
    try:
        # Use legacy text function so tests can monkeypatch it
        raw_response = llm_client.get_keywords_text(prompt)
        # parse_keywords_from_model can handle wrapped JSON / prose
        parsed = parse_keywords_from_model(raw_response)
        return validate_keywords_response(parsed)
    except Exception as e:
        print(f"Warning: Error in get_keywords_safe: {e}")
        return SAFE_OUTPUT.copy()

# Convenience function for quick usage
def generate_keywords_simple(business_desc: str) -> Dict[str, Any]:
    """
    Simple function to generate keywords with minimal setup.
    
    Args:
        business_desc: Business description
        
    Returns:
        Keywords dictionary
    """
    service = KeywordService()
    return service.generate_keywords(business_desc)

def generate_brief_with_variant(
    *,
    keyword: str,
    variant: str,
) -> Tuple[str, str, float, Optional[Dict[str, int]]]:
    """
    Generate content brief with timing and usage tracking.
    
    Args:
        keyword: The keyword to generate content brief for
        variant: Prompt variant to use ('A' or 'B')
    
    Returns: 
        Tuple of (output_text, prompt_used, latency_ms, usage_dict)
        usage_dict example: {"prompt_tokens": 123, "completion_tokens": 456}
    """
    prompt = prompt_manager.format_prompt_variant(
        base_name="content_brief",
        variant=variant,
        keyword=keyword,
    )
    
    t0 = time.monotonic()
    
    # Use the existing LLM client to generate content brief with JSON mode
    client = KeywordLLMClient.create_default()
    result = client.generate_content_brief(prompt)
    
    latency_ms = (time.monotonic() - t0) * 1000

    # Normalize output + usage
    # For now, the client returns a string, so we don't have usage data
    # This can be enhanced later when the LLM client returns usage information
    if isinstance(result, dict):
        output = result.get("text") or result.get("output") or ""
        usage = result.get("usage")  # e.g., {"prompt_tokens":..., "completion_tokens":...}
    else:
        output, usage = str(result), None

    return output, prompt, latency_ms, usage


# ------------- SERP Snapshot Utilities ------------------------

import os
import requests
from typing import List, Dict, Any

def fetch_serp_snapshot(keyword: str, country: str = "US", language: str = "en") -> List[Dict[str, Any]]:
    """
    Return top results with keys: title, url, snippet.
    Supports providers via env:
      SERP_PROVIDER = "serper" | "serpapi" | "mock" (default)
      SERP_API_KEY  = "<key>"
    """
    provider = os.getenv("SERP_PROVIDER", "mock").lower()
    api_key  = os.getenv("SERP_API_KEY", "")

    try:
        if provider == "serper" and api_key:
            # https://serper.dev/ (simple, cheap)
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": keyword, "gl": country, "hl": language, "num": 5},
                timeout=12
            )
            resp.raise_for_status()
            js = resp.json()
            items = js.get("organic", [])[:5]
            return [{"title": it.get("title"),
                     "url":   it.get("link"),
                     "snippet": it.get("snippet")} for it in items]

        if provider == "serpapi" and api_key:
            # https://serpapi.com/
            resp = requests.get(
                "https://serpapi.com/search.json",
                params={"q": keyword, "hl": language, "gl": country, "num": 5, "api_key": api_key},
                timeout=12
            )
            resp.raise_for_status()
            js = resp.json()
            items = js.get("organic_results", [])[:5]
            return [{"title": it.get("title"),
                     "url":   it.get("link"),
                     "snippet": it.get("snippet") or it.get("description")} for it in items]

    except Exception:
        # fall through to mock on any error
        pass

    # Mock fallback (works offline / no key)
    base = keyword.lower()[:30] or "your topic"
    return [
        {"title": f"{base} – community thread", "url": "https://reddit.com/r/example", "snippet": "User opinions and short answers."},
        {"title": f"Quick guide to {base}", "url": "https://example.com/quick-guide", "snippet": "A short guide updated in 2020."},
        {"title": f"{base} explained", "url": "https://example.org/what-is", "snippet": "Definition and basics."},
        {"title": f"Top 10 {base}", "url": "https://blog.example.com/top-10", "snippet": "Roundup with brief descriptions."},
        {"title": f"{base} buyer's checklist", "url": "https://shop.example.com/checklist", "snippet": "Key things to consider."},
    ]
