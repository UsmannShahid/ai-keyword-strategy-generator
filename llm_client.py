# llm_client.py
"""
OpenAI LLM client for keyword generation.
Handles API communication, prompt building, and response processing.
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class KeywordLLMClient:
    """OpenAI client specifically configured for keyword generation."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 700,
        temperature: float = 0.5
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (if None, loads from environment)
            model: Model to use for generation
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0 = deterministic, 1.0 = creative)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        if not self.api_key.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format. Keys should start with 'sk-'")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def build_keyword_prompt(
        self, 
        business_desc: str, 
        industry: str = "", 
        audience: str = "", 
        location: str = ""
    ) -> str:
        """
        Build a comprehensive prompt for keyword generation.
        
        Args:
            business_desc: Main business description
            industry: Industry context
            audience: Target audience
            location: Geographic location/market
            
        Returns:
            Formatted prompt string
        """
        return f"""
You are an expert SEO specialist. Generate 12 SEO keyword ideas for this business, grouped by search intent.

BUSINESS DETAILS:
- Description: {business_desc}
- Industry: {industry or "Not specified"}
- Target audience: {audience or "General"}
- Location/Market: {location or "Global"}

REQUIREMENTS:
1. Generate exactly 12 keywords total
2. Group by search intent: informational, transactional, branded
3. Include a mix of short-tail and long-tail keywords
4. Consider the target audience and location
5. Return ONLY valid JSON in this exact format:

{{
  "informational": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "transactional": ["keyword5", "keyword6", "keyword7", "keyword8"],
  "branded": ["keyword9", "keyword10", "keyword11", "keyword12"]
}}

Do not include any explanation, code blocks, or additional text.
""".strip()
    
    def generate_keywords_raw(self, prompt: str) -> str:
        """
        Generate keywords using the LLM and return raw response.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Raw response text from the LLM
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an SEO expert. Return only valid JSON with no additional text."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    },
                ],
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def generate_keywords(
        self, 
        business_desc: str, 
        industry: str = "", 
        audience: str = "", 
        location: str = ""
    ) -> str:
        """
        Generate keywords for a business with built-in prompt.
        
        Args:
            business_desc: Main business description
            industry: Industry context
            audience: Target audience  
            location: Geographic location/market
            
        Returns:
            Raw response text from the LLM
        """
        prompt = self.build_keyword_prompt(business_desc, industry, audience, location)
        return self.generate_keywords_raw(prompt)
    
    @classmethod
    def create_default(cls) -> 'KeywordLLMClient':
        """Create a client with default settings."""
        return cls()
    
    def test_connection(self) -> bool:
        """
        Test the OpenAI API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple test call
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
            )
            return bool(response.choices[0].message.content)
        except Exception:
            return False

# Convenience functions for backward compatibility
def get_keywords_text(prompt: str) -> str:
    """
    Legacy function for backward compatibility.
    Uses default client to generate keywords.
    """
    client = KeywordLLMClient.create_default()
    return client.generate_keywords_raw(prompt)

def build_prompt(business_desc: str, industry: str, audience: str, location: str) -> str:
    """
    Legacy function for backward compatibility.
    Build prompt using the new client.
    """
    client = KeywordLLMClient.create_default()
    return client.build_keyword_prompt(business_desc, industry, audience, location)
