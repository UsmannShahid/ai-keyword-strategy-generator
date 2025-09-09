"""
Serper.dev API client for SERP data
"""

import os
import httpx
import asyncio
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SerperClient:
    """Client for Serper.dev Google Search API"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=10.0)
        return self.client
    
    async def close(self):
        """Close httpx client"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def search(
        self, 
        query: str, 
        country: str = "US", 
        language: str = "en",
        num_results: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Perform Google search via Serper.dev
        
        Args:
            query: Search query
            country: Country code (US, GB, etc.)
            language: Language code (en, es, fr, etc.)  
            num_results: Number of results (max 10 for free tier)
        
        Returns:
            SERP data or None if failed
        """
        
        if not self.api_key:
            logger.warning("SERPER_API_KEY not found - SERP analysis disabled")
            return None
        
        try:
            client = await self._get_client()
            
            # Prepare request
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "gl": country.lower(),  # geolocation
                "hl": language.lower(),  # host language  
                "num": min(num_results, 10)  # limit to 10 for free tier
            }
            
            # Make API request
            response = await client.post(
                f"{self.base_url}/search",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Serper API success: {query} ({len(data.get('organic', []))} results)")
                return data
            else:
                logger.error(f"Serper API error {response.status_code}: {response.text}")
                return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Serper API timeout for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Serper API error: {e}")
            return None
    
    def analyze_search_intent(self, query: str, serp_data: Dict[str, Any]) -> str:
        """
        Analyze search intent from query and SERP data
        
        Returns: informational, commercial, transactional, navigational
        """
        
        query_lower = query.lower()
        organic_results = serp_data.get('organic', [])
        
        # Transactional indicators
        transactional_keywords = [
            'buy', 'purchase', 'order', 'shop', 'price', 'cost', 'cheap', 
            'discount', 'deal', 'sale', 'coupon', 'best price'
        ]
        
        # Commercial indicators  
        commercial_keywords = [
            'review', 'comparison', 'vs', 'best', 'top', 'compare',
            'alternative', 'option', 'recommendation'
        ]
        
        # Informational indicators
        informational_keywords = [
            'how', 'what', 'why', 'when', 'where', 'guide', 'tutorial',
            'learn', 'definition', 'meaning', 'explain'
        ]
        
        # Check query for intent signals
        if any(kw in query_lower for kw in transactional_keywords):
            return "transactional"
        
        if any(kw in query_lower for kw in commercial_keywords):
            return "commercial"
        
        if any(kw in query_lower for kw in informational_keywords):
            return "informational"
        
        # Analyze SERP results for additional signals
        if organic_results:
            # Check if results contain e-commerce sites
            ecommerce_domains = ['amazon', 'ebay', 'etsy', 'shopify', 'store']
            has_ecommerce = any(
                any(domain in result.get('link', '').lower() for domain in ecommerce_domains)
                for result in organic_results[:5]
            )
            
            if has_ecommerce:
                return "transactional"
            
            # Check titles for commercial intent
            titles_text = ' '.join([r.get('title', '').lower() for r in organic_results[:5]])
            if any(kw in titles_text for kw in commercial_keywords):
                return "commercial"
        
        # Default to informational for ambiguous queries
        return "informational"
    
    def extract_competition_data(self, serp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract competition analysis from SERP data
        
        Returns:
            Dictionary with competition insights
        """
        
        organic_results = serp_data.get('organic', [])
        
        if not organic_results:
            return {"error": "No organic results found"}
        
        # Analyze top 10 competitors
        competitors = []
        domain_frequencies = {}
        
        for i, result in enumerate(organic_results[:10]):
            # Extract domain
            link = result.get('link', '')
            try:
                from urllib.parse import urlparse
                domain = urlparse(link).netloc.lower()
                domain = domain.replace('www.', '')  # normalize
                
                domain_frequencies[domain] = domain_frequencies.get(domain, 0) + 1
                
                competitors.append({
                    "position": i + 1,
                    "title": result.get('title', ''),
                    "domain": domain,
                    "snippet": result.get('snippet', ''),
                    "link": link
                })
            except Exception:
                continue
        
        # Identify dominant domains
        dominant_domains = sorted(domain_frequencies.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate competition level
        unique_domains = len(domain_frequencies)
        competition_level = "high" if unique_domains >= 8 else "medium" if unique_domains >= 5 else "low"
        
        return {
            "total_results": len(competitors),
            "unique_domains": unique_domains,
            "competition_level": competition_level,
            "dominant_domains": dominant_domains,
            "top_competitors": competitors[:5],  # Top 5 for analysis
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

# Global client instance
serper_client = SerperClient()

# Cleanup function for FastAPI shutdown
async def cleanup_serper():
    """Cleanup function for app shutdown"""
    await serper_client.close()