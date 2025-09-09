#!/usr/bin/env python3
"""
Quick Wins Finder - Free Version API (Redis-Only Version)
Simplified FastAPI backend with Redis caching, no PostgreSQL
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

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Redis connection
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("REDIS_URL")
redis_client = None

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Quick Wins Finder API (Free - Redis Version)",
    description="Simplified API with Redis caching and rate limiting",
    version="1.1.0"
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

# Models
class Keyword(BaseModel):
    keyword: str
    volume: Optional[int] = 0
    cpc: Optional[float] = 0.0
    competition: Optional[float] = 0.0
    opportunity_score: Optional[int] = 0
    is_quick_win: bool = False

class KeywordRequest(BaseModel):
    topic: str
    user_id: str
    user_plan: str = "free"
    max_results: int = 10
    industry: Optional[str] = None
    audience: Optional[str] = None
    country: str = "US"
    language: str = "en"

class Brief(BaseModel):
    topic: str
    summary: str

class BriefRequest(BaseModel):
    keyword: str
    user_id: str
    user_plan: str = "free"
    variant: str = "a"

# Redis helper functions
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

# Helper functions
async def generate_keywords(topic: str, industry: str = "", audience: str = "", max_results: int = 10) -> List[Keyword]:
    """Generate keywords with Redis caching"""
    
    # Check cache first
    cache_key = generate_cache_key("keywords", topic=topic, industry=industry, audience=audience)
    cached_data = await get_from_cache(cache_key)
    
    if cached_data:
        print(f"🚀 Redis cache hit for keywords: {topic}")
        keywords = []
        for item in cached_data:
            keywords.append(Keyword(**item))
        return keywords[:max_results]
    
    try:
        # Create context-aware prompt
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
        for item in keyword_data:
            # Calculate opportunity score (simple formula)
            volume = item.get('volume', 0)
            competition = item.get('competition', 1.0)
            opportunity_score = int(min(100, max(0, (volume / 100) * (1 - competition) * 10)))
            
            keywords.append(Keyword(
                keyword=item['keyword'],
                volume=item.get('volume', 0),
                cpc=item.get('cpc', 0.0),
                competition=item.get('competition', 1.0),
                opportunity_score=opportunity_score,
                is_quick_win=item.get('is_quick_win', False)
            ))
        
        # Sort by quick wins first, then by opportunity score
        keywords.sort(key=lambda k: (not k.is_quick_win, -k.opportunity_score))
        
        # Cache the results (1 hour)
        keywords_data = [k.dict() for k in keywords]
        await set_cache(cache_key, keywords_data, 3600)
        print(f"✅ Cached keywords in Redis: {topic}")
        
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
                is_quick_win=True
            ),
            Keyword(
                keyword=f"cheap {topic}",
                volume=1200,
                cpc=0.85,
                competition=0.30,
                opportunity_score=70,
                is_quick_win=True
            )
        ]

async def generate_brief(keyword: str) -> str:
    """Generate content brief with Redis caching"""
    
    # Check cache first
    cache_key = generate_cache_key("brief", keyword=keyword)
    cached_brief = await get_from_cache(cache_key)
    
    if cached_brief:
        print(f"🚀 Redis cache hit for brief: {keyword}")
        return cached_brief
    
    try:
        prompt = f"""
Create a comprehensive content brief for the keyword "{keyword}".

Include:
1. Target audience analysis
2. Search intent (informational, commercial, navigational)
3. Content angle recommendations
4. Suggested H2/H3 outline (5-7 sections)
5. Key entities and terms to include
6. FAQ suggestions (3-5 questions)
7. SEO optimization checklist

Make it actionable and specific. Write in a clear, professional tone.
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content strategist and SEO specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        brief_content = response.choices[0].message.content.strip()
        
        # Cache the brief (4 hours)
        await set_cache(cache_key, brief_content, 14400)
        print(f"✅ Cached brief in Redis: {keyword}")
        
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
    return {"message": "Quick Wins Finder API (Free Version - Redis)", "status": "running"}

@app.get("/health")
async def health_check():
    redis_connected = redis_client is not None
    if redis_connected:
        try:
            await redis_client.ping()
            redis_connected = True
        except:
            redis_connected = False
    
    return {
        "ok": True,
        "redis_connected": redis_connected,
        "cache_strategy": "redis_only" if redis_connected else "no_cache"
    }

@app.get("/cache-stats")
async def get_cache_stats():
    """Get caching performance statistics"""
    redis_connected = redis_client is not None
    if redis_connected:
        try:
            await redis_client.ping()
            redis_connected = True
        except:
            redis_connected = False
    
    if redis_connected:
        return {
            "redis_connected": True,
            "cache_strategy": "redis_only",
            "l1_cache": "redis (fast, 1-4h TTL)",
            "benefits": [
                "Sub-millisecond cache hits",
                "Cost-effective scaling",
                "Simple architecture"
            ]
        }
    else:
        return {
            "redis_connected": False,
            "cache_strategy": "no_cache",
            "message": "Redis caching not available - all requests hit OpenAI API"
        }

@app.post("/suggest-keywords/")
@limiter.limit("10/minute")  # Basic rate limiting
async def suggest_keywords(request: Request, keywords_request: KeywordRequest):
    """Generate keyword suggestions with Redis caching"""
    
    if not keywords_request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    
    # Limit to 10 for free version
    max_results = min(keywords_request.max_results, 10)
    
    try:
        keywords = await generate_keywords(
            topic=keywords_request.topic,
            industry=keywords_request.industry or "",
            audience=keywords_request.audience or "",
            max_results=max_results
        )
        
        return {
            "keywords": [k.dict() for k in keywords],
            "total": len(keywords),
            "quick_wins": len([k for k in keywords if k.is_quick_win]),
            "cached": True if redis_client else False
        }
        
    except Exception as e:
        print(f"Error in suggest_keywords: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate keywords")

@app.post("/generate-brief/")
@limiter.limit("5/minute")  # Basic rate limiting
async def generate_content_brief(request: Request, brief_request: BriefRequest):
    """Generate content brief with Redis caching"""
    
    if not brief_request.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    try:
        brief_content = await generate_brief(brief_request.keyword)
        
        brief = Brief(
            topic=brief_request.keyword,
            summary=brief_content
        )
        
        return {
            "brief": brief.dict(),
            "cached": True if redis_client else False
        }
        
    except Exception as e:
        print(f"Error in generate_brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate brief")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)