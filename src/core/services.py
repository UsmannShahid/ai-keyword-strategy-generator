"""
High-level service functions for keyword generation.
Coordinates between LLM client and parsing logic.
"""

import json
import time
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
import os

# Simple service functions for now - can be expanded later
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
    # Placeholder implementation
    prompt = f"Generate writer notes for keyword: {keyword}"
    notes = {"notes": f"Writer notes for {keyword}", "variant": variant}
    return notes, True, prompt, None

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
    """
    t0 = time.monotonic()
    
    # Get OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        output = f"# Content Brief for '{keyword}'\n\n**Error**: OpenAI API key not configured."
        return output, "No API key", 0, None
    
    client = OpenAI(api_key=api_key)
    
    # Variant-specific prompts
    if variant == "A":
        prompt = f"""
        Create a comprehensive SEO content brief for the keyword: "{keyword}"
        
        Include:
        1. **Title Tag** (60 chars max, include target keyword)
        2. **Meta Description** (160 chars max)
        3. **Content Outline** (H1, H2, H3 structure)
        4. **Target Word Count**
        5. **Key Entities** to mention
        6. **Internal Link Opportunities**
        7. **FAQ Section** (3-5 questions)
        8. **Call-to-Action Ideas**
        
        Focus on search intent and user experience.
        """
    else:  # Variant B
        prompt = f"""
        Write a content brief for "{keyword}" that a freelance writer can easily follow.
        
        Format:
        ## Content Brief: {keyword}
        
        **Primary Goal**: [What should this content achieve?]
        **Target Audience**: [Who is this for?]
        **Tone**: [Professional/Casual/Expert]
        **Content Structure**:
        - Introduction (hook + preview)
        - Main sections (3-5 key topics)
        - Conclusion with clear next steps
        
        **SEO Requirements**:
        - Target keyword: "{keyword}"
        - Related keywords: [list 5-8 variations]
        - Meta title and description
        
        **Writer Notes**: [Any specific instructions or tips]
        """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=1500
        )
        
        output = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        } if response.usage else None
        
    except Exception as e:
        output = f"# Content Brief for '{keyword}'\n\n**Error generating content**: {str(e)}"
        usage = None
    
    latency_ms = (time.monotonic() - t0) * 1000
    return output, prompt, latency_ms, usage

def fetch_serp_snapshot(keyword: str, country: str = "US", language: str = "en") -> list:
    """
    Return top results with keys: title, url, snippet.
    Mock implementation for now.
    """
    base = keyword.lower()[:30] or "your topic"
    return [
        {"title": f"{base} – community thread", "url": "https://reddit.com/r/example", "snippet": "User opinions and short answers."},
        {"title": f"Quick guide to {base}", "url": "https://example.com/quick-guide", "snippet": "A short guide updated in 2020."},
        {"title": f"{base} explained", "url": "https://example.org/what-is", "snippet": "Definition and basics."},
        {"title": f"Top 10 {base}", "url": "https://blog.example.com/top-10", "snippet": "Roundup with brief descriptions."},
        {"title": f"{base} buyer's checklist", "url": "https://shop.example.com/checklist", "snippet": "Key things to consider."},
    ]

class KeywordService:
    """Service class for keyword generation operations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def generate_keywords(
        self, 
        business_desc: str, 
        industry: str = "", 
        audience: str = "", 
        location: str = "",
        prompt_template: str = "default_seo"
    ) -> Dict[str, Any]:
        """Generate keywords for a business with quick-win scores."""
        if not self.client:
            # Fallback with realistic mock data
            return {
                "informational": [
                    {"keyword": f"how to choose {business_desc}", "volume": 850, "difficulty": 45, "quick_win_score": 72},
                    {"keyword": f"{business_desc} guide for beginners", "volume": 620, "difficulty": 38, "quick_win_score": 78},
                    {"keyword": f"what is {business_desc}", "volume": 1200, "difficulty": 55, "quick_win_score": 65}
                ],
                "transactional": [
                    {"keyword": f"buy {business_desc} online", "volume": 940, "difficulty": 42, "quick_win_score": 75},
                    {"keyword": f"best {business_desc} deals", "volume": 720, "difficulty": 35, "quick_win_score": 82},
                    {"keyword": f"affordable {business_desc}", "volume": 580, "difficulty": 30, "quick_win_score": 85}
                ],
                "branded": [
                    {"keyword": f"{business_desc} reviews 2024", "volume": 450, "difficulty": 28, "quick_win_score": 88},
                    {"keyword": f"{business_desc} vs competitors", "volume": 380, "difficulty": 40, "quick_win_score": 76}
                ]
            }
        
        try:
            # Real API call with structured prompt
            prompt = f"""
            Generate 8-12 SEO keywords for this business: {business_desc}
            Industry: {industry or 'general'}
            Audience: {audience or 'general consumers'}
            Location: {location or 'global'}
            
            Return a JSON object with this exact structure:
            {{
                "informational": [
                    {{"keyword": "how to use [product]", "volume": 850, "difficulty": 45, "quick_win_score": 72}}
                ],
                "transactional": [
                    {{"keyword": "buy [product] online", "volume": 940, "difficulty": 42, "quick_win_score": 75}}
                ],
                "branded": [
                    {{"keyword": "[brand] reviews", "volume": 450, "difficulty": 28, "quick_win_score": 88}}
                ]
            }}
            
            Quick-win score = (volume/10) + (100-difficulty). Higher is better.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"API error: {e}")
            # Fallback to mock data
            return self.generate_keywords(business_desc, industry, audience, location, prompt_template)