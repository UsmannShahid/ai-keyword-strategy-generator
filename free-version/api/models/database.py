"""
Database models for storing queries and cache
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.sql import func
from core.database import Base


class KeywordQuery(Base):
    """Store user keyword queries for analytics and caching"""
    __tablename__ = "keyword_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    topic = Column(String(200), index=True)
    industry = Column(String(100))
    audience = Column(String(100))
    country = Column(String(10), default="US")
    language = Column(String(10), default="en")
    user_plan = Column(String(50), default="free")
    
    # Store the generated keywords as JSON
    keywords_data = Column(JSON)
    total_keywords = Column(Integer, default=0)
    quick_wins_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KeywordCache(Base):
    """Cache keyword results to reduce API calls"""
    __tablename__ = "keyword_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cache key components
    topic = Column(String(200), index=True)
    industry = Column(String(100), default="")
    audience = Column(String(100), default="")
    country = Column(String(10), default="US")
    language = Column(String(10), default="en")
    
    # Cached data
    keywords_data = Column(JSON)
    total_keywords = Column(Integer, default=0)
    quick_wins_count = Column(Integer, default=0)
    
    # Cache metadata
    hit_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ContentBrief(Base):
    """Store generated content briefs"""
    __tablename__ = "content_briefs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    keyword = Column(String(200), index=True)
    user_plan = Column(String(50), default="free")
    variant = Column(String(10), default="a")
    
    # Brief content
    brief_content = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BriefCache(Base):
    """Cache content briefs to reduce API calls"""
    __tablename__ = "brief_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), index=True, unique=True)
    brief_content = Column(Text)
    
    # Cache metadata
    hit_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserSession(Base):
    """Track user sessions and usage"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    session_id = Column(String(100), index=True)
    
    # Usage tracking
    keywords_generated = Column(Integer, default=0)
    briefs_generated = Column(Integer, default=0)
    
    # Session info
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())


class SerpCache(Base):
    """Cache SERP results from Serper.dev"""
    __tablename__ = "serp_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Search parameters (used as cache key)
    keyword = Column(String(200), index=True)
    country = Column(String(10), default="US")
    language = Column(String(10), default="en")
    
    # SERP data from Serper.dev
    serp_data = Column(JSON)  # Full SERP response
    organic_results = Column(JSON)  # Top 10 organic results
    total_results = Column(Integer, default=0)
    
    # Analysis data
    search_intent = Column(String(50))  # informational, commercial, transactional, navigational
    competition_analysis = Column(JSON)  # Domain authority, content analysis
    
    # Cache metadata
    hit_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())