#!/usr/bin/env python3
"""
Quick Wins Finder - Free Version API
Simplified FastAPI backend for the free version
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import math
from dotenv import load_dotenv
import openai
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

# Import database components
from core.database import get_db
from core.cache_service import CacheService
from core.redis_client import redis_client, get_redis, RedisClient
from core.hybrid_cache import HybridCacheService
from core.rate_limiter import RateLimiter
from models.database import KeywordQuery, ContentBrief, UserSession

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Quick Wins Finder API (Free)",
    description="Simplified API for finding keyword quick wins with Redis caching",
    version="1.1.0"
)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection and services"""
    await redis_client.connect()
    print("🚀 Quick Wins Finder API started with Redis support")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up Redis connection"""
    await redis_client.disconnect()
    print("👋 API shutdown complete")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
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

# Helper functions
async def generate_keywords(topic: str, industry: str = "", audience: str = "", 
                          max_results: int = 10, redis: RedisClient = None) -> List[Keyword]:
    """Generate keywords using GPT-3.5-turbo with hybrid caching (Redis + PostgreSQL)"""
    
    # Use hybrid cache if Redis is available
    if redis and await redis.is_connected():
        hybrid_cache = HybridCacheService(redis)
        
        # Check hybrid cache (Redis L1 + PostgreSQL L2)
        cached_result = await hybrid_cache.get_keywords(
            topic=topic, industry=industry, audience=audience
        )
        
        if cached_result:
            keywords = []
            for item in cached_result["keywords"]:
                keywords.append(Keyword(**item))
            return keywords[:max_results]
    else:
        # Fallback to PostgreSQL only
        cached_result = await CacheService.get_cached_keywords(
            topic=topic, industry=industry, audience=audience
        )
        
        if cached_result:
            print(f"🐘 Using PostgreSQL cached keywords for: {topic}")
            keywords = []
            for item in cached_result["keywords"]:
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
2. Estimated monthly search volume (realistic numbers, prioritize 500-10,000 range)
3. Estimated CPC in USD (0.50-5.00 range)
4. Competition level (0.0-1.0, where 0 = no competition, 1 = maximum competition)
5. Whether it's a "quick win" (use improved criteria below)

ENHANCED Quick Win Criteria (aim for 60-70% quick wins):
- Competition ≤ 0.35 (low competition threshold)
- Volume ≥ 200 (minimum viable volume)
- CPC ≥ 0.75 (indicates commercial value)
- Prefer 3+ word phrases (long-tail advantage)
- Include intent modifiers: "best", "how to", "guide", "cheap", "affordable", "for beginners", "easy", "simple", "under $X", "vs", "review", "comparison", "tools", "software", "free", "tips"

Priority keyword types for quick wins:
- Long-tail informational: "how to [topic] for beginners"
- Comparison keywords: "best [topic] tools under $50"
- Problem-solving: "easy [topic] tips", "simple [topic] guide"
- Local/niche modifiers: "[topic] for small business"
- Alternative searches: "cheap [topic] alternative"

Format as JSON array (ensure 60-70% have is_quick_win: true):
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
        import json
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
            # Enhanced multi-factor opportunity scoring
            volume = item.get('volume', 0)
            competition = item.get('competition', 1.0)
            cpc = item.get('cpc', 0.0)
            keyword_text = item.get('keyword', '')
            is_quick_win = item.get('is_quick_win', False)
            
            # Multi-factor scoring components
            # 1. Volume score (logarithmic scaling, 0-40 points)
            volume_score = min(40, (math.log1p(volume) / math.log1p(10000)) * 40) if volume > 0 else 0
            
            # 2. Competition score (inverted, 0-30 points)
            competition_score = (1 - competition) * 30
            
            # 3. CPC value score (indicates commercial value, 0-15 points)
            cpc_score = min(15, (cpc / 5.0) * 15) if cpc > 0 else 5
            
            # 4. Long-tail bonus (3+ words get bonus, 0-10 points)
            word_count = len(keyword_text.split())
            longtail_bonus = min(10, max(0, (word_count - 2) * 3))
            
            # 5. Intent modifier bonus (commercial intent keywords, 0-5 points)
            intent_words = ['best', 'cheap', 'affordable', 'guide', 'how to', 'tips', 'tools', 
                          'software', 'review', 'comparison', 'vs', 'under', 'for beginners', 
                          'easy', 'simple', 'free']
            intent_bonus = 5 if any(word.lower() in keyword_text.lower() for word in intent_words) else 0
            
            # Calculate final opportunity score (0-100)
            opportunity_score = int(min(100, max(0, 
                volume_score + competition_score + cpc_score + longtail_bonus + intent_bonus
            )))
            
            # Enhanced quick win detection (overrides LLM decision if score is high enough)
            enhanced_quick_win = (
                is_quick_win or  # Trust LLM decision
                (competition <= 0.35 and volume >= 200 and opportunity_score >= 50) or  # Low comp + decent volume + good score
                (competition <= 0.25 and volume >= 100 and opportunity_score >= 40) or  # Very low comp threshold
                (competition <= 0.30 and word_count >= 3 and intent_bonus > 0)         # Long-tail with intent bonus
            )
            
            keywords.append(Keyword(
                keyword=keyword_text,
                volume=volume,
                cpc=cpc,
                competition=competition,
                opportunity_score=opportunity_score,
                is_quick_win=enhanced_quick_win
            ))
        
        # Post-processing: Ensure we have a good ratio of quick wins
        total_keywords = len(keywords)
        quick_wins = [k for k in keywords if k.is_quick_win]
        quick_win_ratio = len(quick_wins) / total_keywords if total_keywords > 0 else 0
        
        # If quick win ratio is too low, promote some high-scoring keywords to quick wins
        if quick_win_ratio < 0.4:  # Target at least 40% quick wins
            non_quick_wins = [k for k in keywords if not k.is_quick_win]
            non_quick_wins.sort(key=lambda k: k.opportunity_score, reverse=True)
            
            needed_quick_wins = int(total_keywords * 0.5) - len(quick_wins)  # Aim for 50%
            for i in range(min(needed_quick_wins, len(non_quick_wins))):
                if non_quick_wins[i].opportunity_score >= 35:  # Only promote reasonably good keywords
                    non_quick_wins[i].is_quick_win = True
        
        # Sort by enhanced criteria: quick wins first, then by opportunity score
        keywords.sort(key=lambda k: (not k.is_quick_win, -k.opportunity_score))
        
        # Cache the results using hybrid cache if available
        keywords_data = [k.dict() for k in keywords]
        quick_wins_count = len([k for k in keywords if k.is_quick_win])
        
        if redis and await redis.is_connected():
            hybrid_cache = HybridCacheService(redis)
            await hybrid_cache.cache_keywords(
                topic=topic,
                keywords_data=keywords_data,
                total=len(keywords),
                quick_wins=quick_wins_count,
                industry=industry,
                audience=audience
            )
        else:
            # Fallback to PostgreSQL only
            await CacheService.cache_keywords(
                topic=topic,
                keywords_data=keywords_data,
                total=len(keywords),
                quick_wins=quick_wins_count,
                industry=industry,
                audience=audience
            )
        
        return keywords[:max_results]
        
    except Exception as e:
        print(f"Error generating keywords: {e}")
        # Fallback keywords for demo
        fallback_keywords = [
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
            ),
            Keyword(
                keyword=f"best {topic}",
                volume=3500,
                cpc=2.10,
                competition=0.80,
                opportunity_score=25,
                is_quick_win=False
            )
        ]
        return fallback_keywords

async def generate_brief(keyword: str, redis: RedisClient = None) -> str:
    """Generate content brief using GPT-3.5-turbo with hybrid caching"""
    
    # Use hybrid cache if Redis is available
    if redis and await redis.is_connected():
        hybrid_cache = HybridCacheService(redis)
        cached_brief = await hybrid_cache.get_brief(keyword)
        if cached_brief:
            return cached_brief
    else:
        # Fallback to PostgreSQL only
        cached_brief = await CacheService.get_cached_brief(keyword)
        if cached_brief:
            print(f"🐘 Using PostgreSQL cached brief for: {keyword}")
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
        
        # Cache the brief using hybrid cache if available
        if redis and await redis.is_connected():
            hybrid_cache = HybridCacheService(redis)
            await hybrid_cache.cache_brief(keyword, brief_content)
        else:
            # Fallback to PostgreSQL only
            await CacheService.cache_brief(keyword, brief_content)
        
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

## Suggested Outline
1. Introduction - What is {keyword}?
2. Key Benefits and Features
3. How to Choose the Right Option
4. Top Recommendations
5. Common Mistakes to Avoid
6. Frequently Asked Questions
7. Conclusion and Next Steps

## Key Terms to Include
- Related keywords and variations
- Industry-specific terminology
- Long-tail keyword phrases

## FAQ Suggestions
- What should I look for in {keyword}?
- How much does {keyword} typically cost?
- What are the main benefits of {keyword}?

## SEO Checklist
- Include target keyword in title and H1
- Use keyword variations in H2/H3 headings
- Add internal and external links
- Optimize meta description
- Include relevant images with alt text
"""

# Routes
@app.get("/")
async def root():
    return {"message": "Quick Wins Finder API (Free Version)", "status": "running"}

@app.get("/health")
async def health_check(redis: RedisClient = Depends(get_redis)):
    redis_status = await redis.is_connected()
    return {
        "ok": True,
        "redis_connected": redis_status,
        "cache_strategy": "hybrid" if redis_status else "postgresql_only"
    }

@app.get("/cache-stats")
async def get_cache_stats(redis: RedisClient = Depends(get_redis)):
    """Get caching performance statistics"""
    if redis and await redis.is_connected():
        hybrid_cache = HybridCacheService(redis)
        return await hybrid_cache.get_cache_stats()
    else:
        return {
            "redis_connected": False,
            "cache_strategy": "postgresql_only",
            "message": "Redis caching not available"
        }

@app.get("/usage/{user_id}")
async def get_user_usage(user_id: str, user_plan: str = "free", 
                        redis: RedisClient = Depends(get_redis)):
    """Get usage statistics for a user"""
    rate_limiter = RateLimiter(redis)
    return await rate_limiter.get_usage_stats(user_id, user_plan)

@app.post("/suggest-keywords/")
async def suggest_keywords(request: KeywordRequest, 
                          db: AsyncSession = Depends(get_db),
                          redis: RedisClient = Depends(get_redis)):
    """Generate keyword suggestions with quick-wins identification"""
    
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    
    # Limit to 10 for free version
    max_results = min(request.max_results, 10)
    
    # Rate limiting
    rate_limiter = RateLimiter(redis)
    await rate_limiter.check_rate_limit(
        request, "keywords", request.user_plan, request.user_id
    )
    
    try:
        keywords = await generate_keywords(
            topic=request.topic,
            industry=request.industry or "",
            audience=request.audience or "",
            max_results=max_results,
            redis=redis
        )
        
        # Store the query in database
        keywords_data = [k.dict() for k in keywords]
        quick_wins_count = len([k for k in keywords if k.is_quick_win])
        
        query_record = KeywordQuery(
            user_id=request.user_id,
            topic=request.topic,
            industry=request.industry or "",
            audience=request.audience or "",
            country=request.country,
            language=request.language,
            user_plan=request.user_plan,
            keywords_data=keywords_data,
            total_keywords=len(keywords),
            quick_wins_count=quick_wins_count
        )
        
        db.add(query_record)
        await db.commit()
        
        return {
            "keywords": [k.dict() for k in keywords],
            "total": len(keywords),
            "quick_wins": len([k for k in keywords if k.is_quick_win])
        }
        
    except Exception as e:
        print(f"Error in suggest_keywords: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate keywords")

@app.post("/generate-brief/")
async def generate_content_brief(request: BriefRequest, 
                                db: AsyncSession = Depends(get_db),
                                redis: RedisClient = Depends(get_redis)):
    """Generate content brief for a specific keyword"""
    
    if not request.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    # Rate limiting
    rate_limiter = RateLimiter(redis)
    await rate_limiter.check_rate_limit(
        request, "briefs", request.user_plan, request.user_id
    )
    
    try:
        brief_content = await generate_brief(request.keyword, redis)
        
        # Store the brief in database
        brief_record = ContentBrief(
            user_id=request.user_id,
            keyword=request.keyword,
            user_plan=request.user_plan,
            variant=request.variant,
            brief_content=brief_content
        )
        
        db.add(brief_record)
        await db.commit()
        
        brief = Brief(
            topic=request.keyword,
            summary=brief_content
        )
        
        return {"brief": brief.dict()}
        
    except Exception as e:
        print(f"Error in generate_brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate brief")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)