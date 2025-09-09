"""
SERP service with caching and analysis
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from models.database import SerpCache
from core.redis_client import RedisClient
from core.serper_client import SerperClient

logger = logging.getLogger(__name__)

class SerpService:
    """Service for SERP data with Redis + PostgreSQL caching"""
    
    def __init__(self, db_session: AsyncSession, redis_client: RedisClient, serper_client: SerperClient):
        self.db = db_session
        self.redis = redis_client
        self.serper = serper_client
    
    def _generate_cache_key(self, keyword: str, country: str = "US", language: str = "en") -> str:
        """Generate cache key for SERP data"""
        key_data = f"serp:{keyword.lower()}:{country.lower()}:{language.lower()}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_serp_data(
        self, 
        keyword: str, 
        country: str = "US", 
        language: str = "en",
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get SERP data with caching strategy:
        1. Check Redis (1 hour TTL)
        2. Check PostgreSQL (24 hour TTL) 
        3. Fetch from Serper.dev API
        """
        
        cache_key = self._generate_cache_key(keyword, country, language)
        redis_key = f"serp:{cache_key}"
        
        # 1. Try Redis cache first (fast)
        if not force_refresh:
            try:
                cached_data = await self.redis.get(redis_key)
                if cached_data:
                    logger.info(f"🚀 Redis SERP cache hit: {keyword}")
                    return cached_data
            except Exception as e:
                logger.warning(f"Redis SERP get error: {e}")
        
        # 2. Try PostgreSQL cache (24h TTL)
        if not force_refresh:
            try:
                stmt = select(SerpCache).where(
                    SerpCache.keyword == keyword.lower(),
                    SerpCache.country == country.upper(),
                    SerpCache.language == language.lower(),
                    SerpCache.updated_at > datetime.utcnow() - timedelta(hours=24)
                )
                result = await self.db.execute(stmt)
                cached_serp = result.scalar_one_or_none()
                
                if cached_serp:
                    logger.info(f"📊 PostgreSQL SERP cache hit: {keyword}")
                    
                    # Update hit count
                    cached_serp.hit_count += 1
                    await self.db.commit()
                    
                    serp_data = {
                        "organic": cached_serp.organic_results,
                        "serp_data": cached_serp.serp_data,
                        "search_intent": cached_serp.search_intent,
                        "competition_analysis": cached_serp.competition_analysis,
                        "total_results": cached_serp.total_results,
                        "cached": True,
                        "cache_source": "postgresql"
                    }
                    
                    # Store in Redis for faster future access (1 hour)
                    try:
                        await self.redis.set(redis_key, serp_data, expire=3600)
                    except Exception as e:
                        logger.warning(f"Redis SERP set error: {e}")
                    
                    return serp_data
                    
            except Exception as e:
                logger.warning(f"PostgreSQL SERP get error: {e}")
        
        # 3. Fetch from Serper.dev API
        logger.info(f"🔍 Fetching fresh SERP data from Serper.dev: {keyword}")
        
        try:
            serp_response = await self.serper.search(
                query=keyword,
                country=country, 
                language=language,
                num_results=10
            )
            
            if not serp_response:
                logger.warning(f"No SERP data returned for: {keyword}")
                return None
            
            # Analyze search intent and competition
            search_intent = self.serper.analyze_search_intent(keyword, serp_response)
            competition_analysis = self.serper.extract_competition_data(serp_response)
            
            organic_results = serp_response.get('organic', [])[:10]
            total_results = len(organic_results)
            
            # Store in PostgreSQL for long-term caching
            try:
                # Check if entry exists to update vs insert
                stmt = select(SerpCache).where(
                    SerpCache.keyword == keyword.lower(),
                    SerpCache.country == country.upper(), 
                    SerpCache.language == language.lower()
                )
                result = await self.db.execute(stmt)
                existing_serp = result.scalar_one_or_none()
                
                if existing_serp:
                    # Update existing
                    existing_serp.serp_data = serp_response
                    existing_serp.organic_results = organic_results
                    existing_serp.total_results = total_results
                    existing_serp.search_intent = search_intent
                    existing_serp.competition_analysis = competition_analysis
                    existing_serp.hit_count += 1
                    existing_serp.updated_at = datetime.utcnow()
                else:
                    # Create new
                    serp_cache = SerpCache(
                        keyword=keyword.lower(),
                        country=country.upper(),
                        language=language.lower(),
                        serp_data=serp_response,
                        organic_results=organic_results,
                        total_results=total_results,
                        search_intent=search_intent,
                        competition_analysis=competition_analysis
                    )
                    self.db.add(serp_cache)
                
                await self.db.commit()
                logger.info(f"✅ Stored SERP data in PostgreSQL: {keyword}")
                
            except Exception as e:
                logger.error(f"PostgreSQL SERP store error: {e}")
                await self.db.rollback()
            
            # Prepare return data
            serp_data = {
                "organic": organic_results,
                "serp_data": serp_response,
                "search_intent": search_intent,
                "competition_analysis": competition_analysis,
                "total_results": total_results,
                "cached": False,
                "cache_source": "serper_api"
            }
            
            # Store in Redis for fast access (1 hour)
            try:
                await self.redis.set(redis_key, serp_data, expire=3600)
                logger.info(f"✅ Cached SERP data in Redis: {keyword}")
            except Exception as e:
                logger.warning(f"Redis SERP cache error: {e}")
            
            return serp_data
            
        except Exception as e:
            logger.error(f"Error fetching SERP data for {keyword}: {e}")
            return None
    
    async def analyze_keyword_difficulty(self, keyword: str, country: str = "US") -> Dict[str, Any]:
        """
        Analyze keyword difficulty based on SERP data
        """
        
        serp_data = await self.get_serp_data(keyword, country)
        
        if not serp_data:
            return {"error": "Could not fetch SERP data", "difficulty": "unknown"}
        
        competition_analysis = serp_data.get('competition_analysis', {})
        organic_results = serp_data.get('organic', [])
        
        # Calculate difficulty factors
        factors = {
            "total_competitors": len(organic_results),
            "unique_domains": competition_analysis.get('unique_domains', 0),
            "competition_level": competition_analysis.get('competition_level', 'unknown'),
            "dominant_domains": competition_analysis.get('dominant_domains', []),
            "search_intent": serp_data.get('search_intent', 'unknown')
        }
        
        # Simple difficulty scoring
        difficulty_score = 50  # baseline
        
        if factors['competition_level'] == 'high':
            difficulty_score += 30
        elif factors['competition_level'] == 'low':
            difficulty_score -= 20
        
        # Intent affects difficulty
        if factors['search_intent'] == 'transactional':
            difficulty_score += 20
        elif factors['search_intent'] == 'informational':
            difficulty_score -= 10
        
        difficulty_score = max(0, min(100, difficulty_score))  # clamp 0-100
        
        if difficulty_score >= 80:
            difficulty_label = "Very Hard"
        elif difficulty_score >= 60:
            difficulty_label = "Hard"  
        elif difficulty_score >= 40:
            difficulty_label = "Medium"
        elif difficulty_score >= 20:
            difficulty_label = "Easy"
        else:
            difficulty_label = "Very Easy"
        
        return {
            "keyword": keyword,
            "difficulty_score": difficulty_score,
            "difficulty_label": difficulty_label,
            "factors": factors,
            "recommendations": self._get_difficulty_recommendations(difficulty_score, factors)
        }
    
    def _get_difficulty_recommendations(self, score: int, factors: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on difficulty analysis"""
        
        recommendations = []
        
        if score >= 80:
            recommendations.extend([
                "Consider long-tail variations of this keyword",
                "Focus on local or niche modifiers",
                "Build topical authority before targeting this keyword"
            ])
        elif score >= 60:
            recommendations.extend([
                "Target with high-quality, comprehensive content",
                "Consider supporting content cluster strategy",
                "Monitor competitor content gaps"
            ])
        elif score >= 40:
            recommendations.extend([
                "Good opportunity with proper content strategy",
                "Focus on user intent and comprehensive coverage",
                "Consider seasonal trends"
            ])
        else:
            recommendations.extend([
                "Excellent quick-win opportunity",
                "Can rank with basic optimization",
                "Consider expanding to related keywords"
            ])
        
        # Intent-specific recommendations
        intent = factors.get('search_intent', '')
        if intent == 'transactional':
            recommendations.append("Focus on conversion-optimized landing pages")
        elif intent == 'commercial':
            recommendations.append("Create comparison and review content")
        elif intent == 'informational':
            recommendations.append("Develop comprehensive how-to and guide content")
        
        return recommendations[:4]  # Limit to top 4 recommendations