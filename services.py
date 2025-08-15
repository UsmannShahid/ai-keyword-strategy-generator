# services.py
"""
High-level service functions for keyword generation.
Coordinates between LLM client and parsing logic.
"""

from __future__ import annotations
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

from typing import List, Dict, Any

def fetch_serp_snapshot(keyword: str, country: str = "US", language: str = "en") -> List[Dict[str, Any]]:
    """
    Return top results with at least: title, url, snippet.
    Replace the stub with your actual SERP client call.
    """
    # TODO: plug in your real SERP provider here:
    # results = serp_client.search(q=keyword, gl=country, hl=language, num=5)
    # return [{"title": r.title, "url": r.link, "snippet": r.snippet} for r in results]
    return []  # safe default until wired
