"""
Caching service for keywords and content briefs
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import hashlib
import json

from models.database import KeywordCache, BriefCache
from core.database import async_session


class CacheService:
    """Service for handling keyword and brief caching"""
    
    @staticmethod
    def _generate_cache_key(topic: str, industry: str = "", audience: str = "", 
                          country: str = "US", language: str = "en") -> str:
        """Generate a consistent cache key"""
        key_data = f"{topic.lower()}:{industry.lower()}:{audience.lower()}:{country}:{language}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    async def get_cached_keywords(topic: str, industry: str = "", audience: str = "", 
                                country: str = "US", language: str = "en") -> Optional[Dict[str, Any]]:
        """Get cached keyword results"""
        async with async_session() as session:
            try:
                # Check if we have a recent cache entry (within 24 hours)
                cache_expiry = datetime.utcnow() - timedelta(hours=24)
                
                result = await session.execute(
                    select(KeywordCache).where(
                        and_(
                            KeywordCache.topic == topic.lower(),
                            KeywordCache.industry == industry.lower(),
                            KeywordCache.audience == audience.lower(),
                            KeywordCache.country == country,
                            KeywordCache.language == language,
                            KeywordCache.updated_at > cache_expiry
                        )
                    )
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    # Update hit count
                    cache_entry.hit_count += 1
                    cache_entry.updated_at = datetime.utcnow()
                    await session.commit()
                    
                    return {
                        "keywords": cache_entry.keywords_data,
                        "total": cache_entry.total_keywords,
                        "quick_wins": cache_entry.quick_wins_count,
                        "cached": True
                    }
                
                return None
                
            except Exception as e:
                print(f"Error getting cached keywords: {e}")
                await session.rollback()
                return None
    
    @staticmethod
    async def cache_keywords(topic: str, keywords_data: List[Dict], total: int, 
                           quick_wins: int, industry: str = "", audience: str = "", 
                           country: str = "US", language: str = "en"):
        """Cache keyword results"""
        async with async_session() as session:
            try:
                # Check if entry already exists
                existing = await session.execute(
                    select(KeywordCache).where(
                        and_(
                            KeywordCache.topic == topic.lower(),
                            KeywordCache.industry == industry.lower(),
                            KeywordCache.audience == audience.lower(),
                            KeywordCache.country == country,
                            KeywordCache.language == language
                        )
                    )
                )
                cache_entry = existing.scalar_one_or_none()
                
                if cache_entry:
                    # Update existing entry
                    cache_entry.keywords_data = keywords_data
                    cache_entry.total_keywords = total
                    cache_entry.quick_wins_count = quick_wins
                    cache_entry.hit_count += 1
                    cache_entry.updated_at = datetime.utcnow()
                else:
                    # Create new entry
                    cache_entry = KeywordCache(
                        topic=topic.lower(),
                        industry=industry.lower(),
                        audience=audience.lower(),
                        country=country,
                        language=language,
                        keywords_data=keywords_data,
                        total_keywords=total,
                        quick_wins_count=quick_wins
                    )
                    session.add(cache_entry)
                
                await session.commit()
                print(f"✅ Cached keywords for topic: {topic}")
                
            except Exception as e:
                print(f"Error caching keywords: {e}")
                await session.rollback()
    
    @staticmethod
    async def get_cached_brief(keyword: str) -> Optional[str]:
        """Get cached content brief"""
        async with async_session() as session:
            try:
                # Check if we have a recent cache entry (within 7 days)
                cache_expiry = datetime.utcnow() - timedelta(days=7)
                
                result = await session.execute(
                    select(BriefCache).where(
                        and_(
                            BriefCache.keyword == keyword.lower(),
                            BriefCache.updated_at > cache_expiry
                        )
                    )
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    # Update hit count
                    cache_entry.hit_count += 1
                    cache_entry.updated_at = datetime.utcnow()
                    await session.commit()
                    
                    return cache_entry.brief_content
                
                return None
                
            except Exception as e:
                print(f"Error getting cached brief: {e}")
                await session.rollback()
                return None
    
    @staticmethod
    async def cache_brief(keyword: str, brief_content: str):
        """Cache content brief"""
        async with async_session() as session:
            try:
                # Check if entry already exists
                existing = await session.execute(
                    select(BriefCache).where(BriefCache.keyword == keyword.lower())
                )
                cache_entry = existing.scalar_one_or_none()
                
                if cache_entry:
                    # Update existing entry
                    cache_entry.brief_content = brief_content
                    cache_entry.hit_count += 1
                    cache_entry.updated_at = datetime.utcnow()
                else:
                    # Create new entry
                    cache_entry = BriefCache(
                        keyword=keyword.lower(),
                        brief_content=brief_content
                    )
                    session.add(cache_entry)
                
                await session.commit()
                print(f"✅ Cached brief for keyword: {keyword}")
                
            except Exception as e:
                print(f"Error caching brief: {e}")
                await session.rollback()