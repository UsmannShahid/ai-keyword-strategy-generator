# services.py
"""
High-level service functions for keyword generation.
Coordinates between LLM client and parsing logic.
"""

from __future__ import annotations
from typing import Dict, Any
from llm_client import KeywordLLMClient
from parsing import parse_keywords_from_model, validate_keywords_response, SAFE_OUTPUT

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
        location: str = ""
    ) -> Dict[str, Any]:
        """
        Generate and parse keywords for a business.
        
        Args:
            business_desc: Main business description
            industry: Industry context
            audience: Target audience
            location: Geographic location/market
            
        Returns:
            Parsed keywords dictionary with fallback handling
        """
        try:
            # Generate raw response
            raw_response = self.llm_client.generate_keywords(
                business_desc, industry, audience, location
            )
            
            # Parse with robust fallback
            return validate_keywords_response(raw_response)
            
        except Exception as e:
            print(f"Warning: Error in keyword generation: {e}")
            return SAFE_OUTPUT.copy()
    
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
        client = KeywordLLMClient.create_default()
        raw_response = client.generate_keywords_raw(prompt)
        return validate_keywords_response(raw_response)
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
