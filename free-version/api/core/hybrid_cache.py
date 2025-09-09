"""
Hybrid caching service using Redis (fast) + PostgreSQL (persistent)
"""

import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from core.redis_client import RedisClient
from core.cache_service import CacheService

logger = logging.getLogger(__name__)

class HybridCacheService:
    """
    Two-tier caching strategy:
    1. Redis (L1) - Fast, short-term (minutes to hours)
    2. PostgreSQL (L2) - Persistent, long-term (hours to days)
    """
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.postgres_cache = CacheService()
    
    def _generate_redis_key(self, prefix: str, **kwargs) -> str:
        """Generate Redis key from parameters"""
        key_data = ":".join(f"{k}={str(v).lower()}" for k, v in sorted(kwargs.items()) if v)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"{prefix}:{key_hash}"
    
    async def get_keywords(self, topic: str, industry: str = "", audience: str = "", 
                          country: str = "US", language: str = "en") -> Optional[Dict[str, Any]]:
        """Get keywords with two-tier caching"""
        
        # L1 Cache: Check Redis (fastest, 1 hour TTL)
        redis_key = self._generate_redis_key(
            "keywords", 
            topic=topic, industry=industry, audience=audience,
            country=country, language=language
        )
        
        cached_data = await self.redis.get(redis_key)
        if cached_data:
            logger.info(f"🚀 Redis cache hit for keywords: {topic}")
            return cached_data
        
        # L2 Cache: Check PostgreSQL (persistent, 24 hour TTL)
        pg_data = await self.postgres_cache.get_cached_keywords(
            topic, industry, audience, country, language
        )
        
        if pg_data:
            logger.info(f"🐘 PostgreSQL cache hit for keywords: {topic}")
            # Store in Redis for faster future access (1 hour)
            await self.redis.set(redis_key, pg_data, expire=3600)
            return pg_data
        
        logger.info(f"❌ Cache miss for keywords: {topic}")
        return None
    
    async def cache_keywords(self, topic: str, keywords_data: List[Dict], 
                           total: int, quick_wins: int, industry: str = "", 
                           audience: str = "", country: str = "US", language: str = "en"):
        """Cache keywords in both Redis and PostgreSQL"""
        
        cache_data = {
            "keywords": keywords_data,
            "total": total,
            "quick_wins": quick_wins,
            "cached": True
        }
        
        # Store in Redis (L1 - fast access, 1 hour)
        redis_key = self._generate_redis_key(
            "keywords",
            topic=topic, industry=industry, audience=audience,
            country=country, language=language
        )
        await self.redis.set(redis_key, cache_data, expire=3600)
        
        # Store in PostgreSQL (L2 - persistent, 24 hours)
        await self.postgres_cache.cache_keywords(
            topic, keywords_data, total, quick_wins, 
            industry, audience, country, language
        )
        
        logger.info(f"✅ Cached keywords in both Redis + PostgreSQL: {topic}")
    
    async def get_brief(self, keyword: str) -> Optional[str]:
        """Get content brief with two-tier caching"""
        
        # L1 Cache: Check Redis (4 hours TTL for briefs)
        redis_key = self._generate_redis_key("brief", keyword=keyword)
        cached_brief = await self.redis.get(redis_key)
        
        if cached_brief:
            logger.info(f"🚀 Redis cache hit for brief: {keyword}")
            return cached_brief
        
        # L2 Cache: Check PostgreSQL (7 days TTL)
        pg_brief = await self.postgres_cache.get_cached_brief(keyword)
        
        if pg_brief:
            logger.info(f"🐘 PostgreSQL cache hit for brief: {keyword}")
            # Store in Redis for faster future access (4 hours)
            await self.redis.set(redis_key, pg_brief, expire=14400)
            return pg_brief
        
        logger.info(f"❌ Cache miss for brief: {keyword}")
        return None
    
    async def cache_brief(self, keyword: str, brief_content: str):
        """Cache brief in both Redis and PostgreSQL"""
        
        # Store in Redis (L1 - fast access, 4 hours)
        redis_key = self._generate_redis_key("brief", keyword=keyword)
        await self.redis.set(redis_key, brief_content, expire=14400)
        
        # Store in PostgreSQL (L2 - persistent, 7 days)
        await self.postgres_cache.cache_brief(keyword, brief_content)
        
        logger.info(f"✅ Cached brief in both Redis + PostgreSQL: {keyword}")
    
    async def invalidate_keywords(self, topic: str, **kwargs):
        """Invalidate keyword cache in both layers"""
        redis_key = self._generate_redis_key("keywords", topic=topic, **kwargs)
        await self.redis.delete(redis_key)
        logger.info(f"🗑️ Invalidated keywords cache: {topic}")
    
    async def invalidate_brief(self, keyword: str):
        """Invalidate brief cache in both layers"""
        redis_key = self._generate_redis_key("brief", keyword=keyword)
        await self.redis.delete(redis_key)
        logger.info(f"🗑️ Invalidated brief cache: {keyword}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        if not await self.redis.is_connected():
            return {"redis_connected": False, "cache_strategy": "postgresql_only"}
        
        # Redis is available
        return {
            "redis_connected": True,
            "cache_strategy": "hybrid",
            "l1_cache": "redis (fast, 1-4h TTL)",
            "l2_cache": "postgresql (persistent, 24h-7d TTL)",
            "benefits": [
                "Sub-millisecond cache hits",
                "Persistent cache across restarts", 
                "Cost-effective scaling",
                "Automatic failover"
            ]
        }