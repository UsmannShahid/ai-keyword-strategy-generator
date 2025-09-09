#!/usr/bin/env python3
"""
Quick Wins Finder - SERP Enhanced API
FastAPI backend with SERP analysis, Redis caching, and PostgreSQL
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import openai
from datetime import datetime
import json
import hashlib

# Redis imports
import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.database import get_db
from models.database import Base

# SERP imports
from core.serper_client import serper_client, cleanup_serper
from core.serp_service import SerpService
from core.redis_client import RedisClient

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Redis connection
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("REDIS_URL")
redis_client = None

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Initialize Redis client wrapper
redis_wrapper = RedisClient()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Quick Wins Finder API (SERP Enhanced)",
    description="API with SERP analysis, Redis caching, and keyword difficulty scoring",
    version="1.2.0"
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Connect to Redis on startup"""
    await redis_wrapper.connect()
    print("✅ SERP-enhanced API started with Redis and PostgreSQL support")

@app.on_event("shutdown") 
async def shutdown():
    """Cleanup connections on shutdown"""
    await redis_wrapper.disconnect()
    await cleanup_serper()
    print("🔌 Connections closed")

# Models
class Keyword(BaseModel):
    keyword: str
    volume: Optional[int] = 0
    cpc: Optional[float] = 0.0
    competition: Optional[float] = 0.0
    opportunity_score: Optional[int] = 0
    is_quick_win: bool = False
    difficulty_score: Optional[int] = None
    search_intent: Optional[str] = None
    serp_enhanced: bool = False

class KeywordRequest(BaseModel):
    topic: str
    user_id: str
    user_plan: str = "free"
    max_results: int = 10
    industry: Optional[str] = None
    audience: Optional[str] = None
    country: str = "US"
    language: str = "en"
    use_serp_analysis: bool = True

class Brief(BaseModel):
    topic: str
    summary: str

class BriefRequest(BaseModel):
    keyword: str
    user_id: str
    user_plan: str = "free"
    variant: str = "a"
    use_serp_analysis: bool = True

# Redis helper functions (keep existing for fallback)
async def get_from_cache(key: str):
    """Get data from Redis cache"""
    if not redis_client:
        return None
    
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis get error: {e}")
    return None

async def set_cache(key: str, data, expire_seconds: int = 3600):
    """Set data in Redis cache"""
    if not redis_client:
        return False
    
    try:
        await redis_client.setex(key, expire_seconds, json.dumps(data))
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False

def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key"""
    key_data = ":".join(f"{k}={str(v).lower()}" for k, v in sorted(kwargs.items()) if v)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
    return f"{prefix}:{key_hash}"

# Database dependency
async def get_db_session():
    """Get database session"""
    if not AsyncSessionLocal:
        yield None
        return
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Enhanced keyword generation with SERP analysis
async def generate_keywords_with_serp(
    topic: str, 
    industry: str = "", 
    audience: str = "", 
    country: str = "US", 
    language: str = "en",
    max_results: int = 10,
    use_serp_analysis: bool = True
) -> List[Keyword]:
    """Generate keywords enhanced with SERP analysis"""
    
    # Check cache first
    cache_key = generate_cache_key("keywords_serp", topic=topic, industry=industry, audience=audience, country=country)
    cached_data = await get_from_cache(cache_key)
    
    if cached_data:
        print(f"🚀 Redis cache hit for SERP keywords: {topic}")
        keywords = []
        for item in cached_data:
            keywords.append(Keyword(**item))
        return keywords[:max_results]
    
    try:
        # Step 1: Generate initial keywords with OpenAI
        context = f"Industry: {industry or 'General'}, Audience: {audience or 'General public'}"
        
        prompt = f"""
Generate {max_results} keyword variations for the topic "{topic}".

Context: {context}

For each keyword, provide:
1. The keyword phrase
2. Estimated monthly search volume (realistic numbers)
3. Estimated CPC in USD
4. Competition level (0.0-1.0, where 0 = no competition, 1 = maximum competition)
5. Whether it's a "quick win" (low competition + decent volume)

Quick win criteria:
- Competition < 0.4
- Volume > 100
- Contains modifiers like "cheap", "best", "under $X", "for beginners", etc.

Format as JSON array:
[{{"keyword": "example", "volume": 1200, "cpc": 1.50, "competition": 0.3, "is_quick_win": true}}]
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a keyword research expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            keyword_data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response if wrapped in text
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                keyword_data = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse keyword data")
        
        keywords = []
        
        # Step 2: Enhance with SERP analysis if enabled and DB available
        db_session = None
        serp_service = None
        
        if use_serp_analysis and AsyncSessionLocal:
            try:
                db_session = AsyncSessionLocal()
                serp_service = SerpService(db_session, redis_wrapper, serper_client)
            except Exception as e:
                print(f"Could not initialize SERP service: {e}")
        
        for item in keyword_data:
            keyword_text = item['keyword']
            
            # Calculate base opportunity score
            volume = item.get('volume', 0)
            competition = item.get('competition', 1.0)
            opportunity_score = int(min(100, max(0, (volume / 100) * (1 - competition) * 10)))
            
            # Initialize keyword object
            keyword_obj = Keyword(
                keyword=keyword_text,
                volume=item.get('volume', 0),
                cpc=item.get('cpc', 0.0),
                competition=item.get('competition', 1.0),
                opportunity_score=opportunity_score,
                is_quick_win=item.get('is_quick_win', False),
                serp_enhanced=False
            )
            
            # Enhance with SERP analysis for top keywords
            if serp_service and len(keywords) < 5:  # Only analyze top 5 to save API calls
                try:
                    print(f"🔍 Analyzing SERP for: {keyword_text}")
                    difficulty_analysis = await serp_service.analyze_keyword_difficulty(keyword_text, country)
                    
                    if not difficulty_analysis.get('error'):
                        keyword_obj.difficulty_score = difficulty_analysis.get('difficulty_score', 50)
                        keyword_obj.search_intent = difficulty_analysis.get('factors', {}).get('search_intent', 'unknown')
                        keyword_obj.serp_enhanced = True
                        
                        # Adjust quick_win status based on SERP difficulty
                        if keyword_obj.difficulty_score <= 30 and volume > 100:
                            keyword_obj.is_quick_win = True
                        elif keyword_obj.difficulty_score >= 70:
                            keyword_obj.is_quick_win = False
                        
                        # Adjust opportunity score with SERP data
                        serp_factor = (100 - keyword_obj.difficulty_score) / 100
                        keyword_obj.opportunity_score = int(keyword_obj.opportunity_score * 0.7 + (serp_factor * 100) * 0.3)
                        
                        print(f"✅ SERP enhanced: {keyword_text} (difficulty: {keyword_obj.difficulty_score})")
                
                except Exception as e:
                    print(f"SERP analysis failed for {keyword_text}: {e}")
            
            keywords.append(keyword_obj)
        
        # Close database session
        if db_session:
            await db_session.close()
        
        # Sort by enhanced opportunity score, then by quick wins
        keywords.sort(key=lambda k: (not k.is_quick_win, -k.opportunity_score))
        
        # Cache the results (2 hours for SERP-enhanced data)
        keywords_data = [k.dict() for k in keywords]
        await set_cache(cache_key, keywords_data, 7200)
        print(f"✅ Cached SERP-enhanced keywords: {topic}")
        
        return keywords[:max_results]
        
    except Exception as e:
        print(f"Error generating keywords: {e}")
        # Fallback keywords for demo
        return [
            Keyword(
                keyword=f"{topic} for beginners",
                volume=800,
                cpc=1.20,
                competition=0.25,
                opportunity_score=75,
                is_quick_win=True,
                serp_enhanced=False
            ),
            Keyword(
                keyword=f"cheap {topic}",
                volume=1200,
                cpc=0.85,
                competition=0.30,
                opportunity_score=70,
                is_quick_win=True,
                serp_enhanced=False
            )
        ]

async def generate_brief_with_serp(keyword: str, country: str = "US", use_serp_analysis: bool = True) -> str:
    """Generate content brief enhanced with SERP analysis"""
    
    # Check cache first
    cache_key = generate_cache_key("brief_serp", keyword=keyword, country=country)
    cached_brief = await get_from_cache(cache_key)
    
    if cached_brief:
        print(f"🚀 Redis cache hit for SERP brief: {keyword}")
        return cached_brief
    
    try:
        serp_context = ""
        
        # Get SERP analysis if enabled and DB available
        if use_serp_analysis and AsyncSessionLocal:
            try:
                db_session = AsyncSessionLocal()
                serp_service = SerpService(db_session, redis_wrapper, serper_client)
                
                serp_data = await serp_service.get_serp_data(keyword, country)
                
                if serp_data and not serp_data.get('error'):
                    search_intent = serp_data.get('search_intent', 'informational')
                    competition_analysis = serp_data.get('competition_analysis', {})
                    top_competitors = competition_analysis.get('top_competitors', [])
                    
                    competitor_titles = [comp.get('title', '') for comp in top_competitors[:3]]
                    
                    serp_context = f"""
SERP Analysis for "{keyword}":
- Search Intent: {search_intent}
- Competition Level: {competition_analysis.get('competition_level', 'unknown')}
- Top competing content: {', '.join(competitor_titles)}
- Unique domains: {competition_analysis.get('unique_domains', 0)}

Use this SERP data to create content that can outrank competitors.
"""
                    print(f"✅ SERP context added for brief: {keyword}")
                
                await db_session.close()
                
            except Exception as e:
                print(f"SERP analysis failed for brief {keyword}: {e}")
        
        # Generate enhanced brief
        prompt = f"""
Create a comprehensive content brief for the keyword "{keyword}".

{serp_context}

Include:
1. Target audience analysis
2. Search intent (informational, commercial, navigational)
3. Content angle recommendations based on competitor analysis
4. Suggested H2/H3 outline (5-7 sections)
5. Key entities and terms to include
6. FAQ suggestions (3-5 questions)
7. SEO optimization checklist
8. Content differentiation opportunities

Make it actionable and specific. Write in a clear, professional tone.
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content strategist and SEO specialist with access to SERP data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        
        brief_content = response.choices[0].message.content.strip()
        
        # Cache the brief (4 hours for SERP-enhanced briefs)
        await set_cache(cache_key, brief_content, 14400)
        print(f"✅ Cached SERP-enhanced brief: {keyword}")
        
        return brief_content
        
    except Exception as e:
        print(f"Error generating brief: {e}")
        return f"""
# Content Brief: {keyword}

## Target Audience
People searching for "{keyword}" are likely looking for practical information and solutions.

## Search Intent  
Mixed intent - both informational and commercial. Users want to learn and potentially purchase.

## Content Angle
Focus on practical, actionable advice with clear benefits and solutions.
"""

# Routes
@app.get("/")
async def root():
    return {"message": "Quick Wins Finder API (SERP Enhanced)", "status": "running"}

@app.get("/health")
async def health_check():
    redis_connected = await redis_wrapper.is_connected()
    db_connected = DATABASE_URL is not None
    serper_available = os.getenv("SERPER_API_KEY") is not None
    
    return {
        "ok": True,
        "redis_connected": redis_connected,
        "database_connected": db_connected,
        "serper_available": serper_available,
        "cache_strategy": "redis_postgresql_serp" if redis_connected and db_connected else "redis_only"
    }

@app.post("/suggest-keywords/")
@limiter.limit("8/minute")  # Slightly lower due to SERP API calls
async def suggest_keywords(request: Request, keywords_request: KeywordRequest):
    """Generate keyword suggestions with optional SERP enhancement"""
    
    if not keywords_request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    
    # Limit to 10 for free version
    max_results = min(keywords_request.max_results, 10)
    
    try:
        keywords = await generate_keywords_with_serp(
            topic=keywords_request.topic,
            industry=keywords_request.industry or "",
            audience=keywords_request.audience or "",
            country=keywords_request.country,
            language=keywords_request.language,
            max_results=max_results,
            use_serp_analysis=keywords_request.use_serp_analysis
        )
        
        serp_enhanced_count = len([k for k in keywords if k.serp_enhanced])
        
        return {
            "keywords": [k.dict() for k in keywords],
            "total": len(keywords),
            "quick_wins": len([k for k in keywords if k.is_quick_win]),
            "serp_enhanced": serp_enhanced_count,
            "cached": True if redis_client else False
        }
        
    except Exception as e:
        print(f"Error in suggest_keywords: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate keywords")

@app.post("/generate-brief/")
@limiter.limit("4/minute")  # Lower due to SERP API calls
async def generate_content_brief(request: Request, brief_request: BriefRequest):
    """Generate content brief with optional SERP enhancement"""
    
    if not brief_request.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    try:
        brief_content = await generate_brief_with_serp(
            brief_request.keyword,
            country="US",  # TODO: get from user settings
            use_serp_analysis=brief_request.use_serp_analysis
        )
        
        brief = Brief(
            topic=brief_request.keyword,
            summary=brief_content
        )
        
        return {
            "brief": brief.dict(),
            "serp_enhanced": brief_request.use_serp_analysis,
            "cached": True if redis_client else False
        }
        
    except Exception as e:
        print(f"Error in generate_brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate brief")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)