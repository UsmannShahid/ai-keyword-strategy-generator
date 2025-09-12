#!/usr/bin/env python3
"""
Quick Wins Finder - SERP Enhanced API (Redis-only Version)
FastAPI backend with SERP analysis and Redis caching
"""

from fastapi import FastAPI, HTTPException, Request
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

# SERP imports
import httpx
import asyncio
import logging
import math
from dataclasses import dataclass

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("REDIS_URL")
redis_client = None

if REDIS_URL:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Quick Wins Finder API (SERP Enhanced - Simple)",
    description="API with SERP analysis and Redis caching (no PostgreSQL)",
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

# Simple Serper client
class SimpleSerperClient:
    """Simple Serper.dev client using httpx"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"
    
    async def search(self, query: str, country: str = "US", language: str = "en") -> Optional[dict]:
        """Search using Serper.dev API"""
        
        if not self.api_key:
            logger.warning("SERPER_API_KEY not found - SERP analysis disabled")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "q": query,
                    "gl": country.lower(),
                    "hl": language.lower(),
                    "num": 10
                }
                
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
                    
        except Exception as e:
            logger.error(f"Serper API error: {e}")
            return None
    
    def analyze_search_intent(self, query: str, serp_data: dict) -> str:
        """Analyze search intent from query and SERP data"""
        
        query_lower = query.lower()
        
        # Transactional indicators
        transactional_keywords = ['buy', 'purchase', 'order', 'shop', 'price', 'cost', 'cheap', 'discount', 'deal', 'sale']
        # Commercial indicators  
        commercial_keywords = ['review', 'comparison', 'vs', 'best', 'top', 'compare', 'alternative']
        # Informational indicators
        informational_keywords = ['how', 'what', 'why', 'when', 'where', 'guide', 'tutorial', 'learn']
        
        if any(kw in query_lower for kw in transactional_keywords):
            return "transactional"
        elif any(kw in query_lower for kw in commercial_keywords):
            return "commercial"
        elif any(kw in query_lower for kw in informational_keywords):
            return "informational"
        
        return "informational"  # default
    
    def calculate_difficulty_score(self, serp_data: dict) -> int:
        """Calculate keyword difficulty from SERP data"""
        
        organic_results = serp_data.get('organic', [])
        if not organic_results:
            return 50  # neutral
        
        # Simple difficulty scoring based on domain authority indicators
        high_authority_domains = ['wikipedia', 'amazon', 'youtube', 'facebook', 'linkedin', 'reddit']
        authority_count = 0
        
        for result in organic_results[:10]:
            link = result.get('link', '').lower()
            if any(domain in link for domain in high_authority_domains):
                authority_count += 1
        
        # More authority domains = higher difficulty
        difficulty_score = 30 + (authority_count * 10)  # base 30, +10 per authority domain
        return min(100, max(0, difficulty_score))

# Global Serper client
serper_client = SimpleSerperClient()

# Multi-Factor Scoring System with Dynamic Difficulty Profiles
from typing import Dict, Any, List, Tuple, Literal
import re

DifficultyMode = Literal["easy", "medium", "hard"]

@dataclass(frozen=True)
class MultiFactorParams:
    # Dynamic weights based on difficulty mode
    difficulty_mode: DifficultyMode = "medium"
    
    # Weight ranges for different components (will be adjusted based on mode)
    volume_weight_range: Tuple[float, float] = (0.25, 0.45)      # 25-45%
    competition_weight_range: Tuple[float, float] = (0.20, 0.40) # 20-40%  
    cpc_weight_range: Tuple[float, float] = (0.15, 0.25)        # 15-25%
    longtail_weight_range: Tuple[float, float] = (0.05, 0.15)   # 5-15%
    commercial_weight: float = 0.05                              # 5%
    
    # Volume scoring parameters
    volume_log_base: float = 10.0
    volume_max_score: int = 10000    # Volume that gets max score
    
    # CPC scoring parameters  
    cpc_optimal_range: Tuple[float, float] = (0.5, 3.0)  # Sweet spot for CPC
    cpc_max_score: float = 5.0
    
    # Competition thresholds by difficulty mode (increased for more quick wins)
    easy_max_competition: float = 0.5      # Increased from 0.4
    medium_max_competition: float = 0.7    # Increased from 0.6
    hard_max_competition: float = 1.0      # No filter
    
    # Opportunity score thresholds (0-100 scale)
    excellent_threshold: int = 60    # 60-100: Excellent 
    good_threshold: int = 40         # 40-60: Good
    moderate_threshold: int = 20     # 20-40: Moderate
    # 0-20: Difficult
    
    # Quick win threshold by difficulty mode (lowered for better quick win detection)
    easy_quick_win_threshold: float = 45.0      # Lowered from 65.0
    medium_quick_win_threshold: float = 55.0    # Lowered from 70.0
    hard_quick_win_threshold: float = 65.0      # Lowered from 75.0

def get_difficulty_weights(mode: DifficultyMode) -> Dict[str, float]:
    """Get component weights based on difficulty mode"""
    if mode == "easy":
        return {
            "volume": 0.25,      # 25%
            "competition": 0.45, # 45% - Strong focus on low competition
            "cpc": 0.10,         # 10%
            "longtail": 0.15,    # 15%
            "commercial": 0.05   # 5%
        }
    elif mode == "medium":
        return {
            "volume": 0.35,      # 35% 
            "competition": 0.30, # 30% - Balanced approach
            "cpc": 0.20,         # 20%
            "longtail": 0.10,    # 10%
            "commercial": 0.05   # 5%
        }
    else:  # hard
        return {
            "volume": 0.45,      # 45% - Volume-focused
            "competition": 0.20, # 20%
            "cpc": 0.25,         # 25%
            "longtail": 0.05,    # 5%
            "commercial": 0.05   # 5%
        }

def score_volume(volume: float, params: MultiFactorParams) -> float:
    """Score volume using normalized logarithmic scaling (0-100)"""
    if volume <= 0:
        return 0.0
    
    # Logarithmic scaling with normalization
    log_volume = math.log(max(1, volume), params.volume_log_base)
    log_max = math.log(params.volume_max_score, params.volume_log_base)
    
    score = min(100.0, (log_volume / log_max) * 100.0)
    return score

def score_competition(competition: float) -> float:
    """Score competition (inverted - lower competition = higher score) (0-100)"""
    # Invert competition: 0 competition = 100 points, 1 competition = 0 points
    return (1.0 - min(1.0, max(0.0, competition))) * 100.0

def score_cpc(cpc: float, params: MultiFactorParams) -> float:
    """Score CPC value (0-100) - higher CPC often means commercial value"""
    if cpc <= 0:
        return 0.0
    
    optimal_min, optimal_max = params.cpc_optimal_range
    
    if optimal_min <= cpc <= optimal_max:
        # In optimal range - full score
        return 100.0
    elif cpc < optimal_min:
        # Below optimal - scale from 0 to 100
        return (cpc / optimal_min) * 100.0
    else:
        # Above optimal - diminishing returns
        excess = cpc - optimal_max
        decay_factor = math.exp(-excess / params.cpc_max_score)
        return 100.0 * decay_factor

def score_longtail(keyword: str) -> float:
    """Score long-tail keywords (0-100) - 3+ word keywords get bonus"""
    words = len(keyword.strip().split())
    
    if words >= 5:
        return 100.0  # 5+ words = excellent
    elif words == 4:
        return 80.0   # 4 words = very good
    elif words == 3:
        return 60.0   # 3 words = good
    elif words == 2:
        return 30.0   # 2 words = moderate
    else:
        return 0.0    # 1 word = poor

def classify_search_intent(keyword: str) -> str:
    """Classify search intent into 4 categories with detailed analysis"""
    keyword_lower = keyword.lower()
    words = keyword_lower.split()
    
    # Transactional (Ready to buy/act)
    transactional_signals = ['buy', 'purchase', 'order', 'shop', 'checkout', 'cart', 'pricing', 'price', 'cost', 'deal', 'discount', 'sale', 'coupon', 'offer', 'book', 'hire', 'subscribe']
    
    # Commercial (Comparing/researching before buying)
    commercial_signals = ['best', 'top', 'review', 'reviews', 'compare', 'comparison', 'vs', 'versus', 'alternative', 'alternatives', 'cheap', 'affordable', 'budget', 'premium', 'professional']
    
    # Informational (Learning/how-to)
    informational_signals = ['how', 'what', 'why', 'when', 'where', 'guide', 'tutorial', 'tips', 'learn', 'understand', 'explain', 'meaning', 'definition', 'examples', 'beginner', 'basics', 'setup', 'install']
    
    # Navigational (Looking for specific brand/site)
    navigational_signals = ['login', 'sign in', 'dashboard', 'account', 'portal', 'official', 'website', 'app', 'download']
    
    # Count matches
    transactional_matches = sum(1 for signal in transactional_signals if signal in keyword_lower)
    commercial_matches = sum(1 for signal in commercial_signals if signal in keyword_lower)  
    informational_matches = sum(1 for signal in informational_signals if signal in keyword_lower)
    navigational_matches = sum(1 for signal in navigational_signals if signal in keyword_lower)
    
    # Determine primary intent (highest score wins)
    scores = {
        'Transactional': transactional_matches * 3,  # Weight transactional higher
        'Commercial': commercial_matches * 2,        # Weight commercial moderately  
        'Informational': informational_matches * 1,  # Base weight
        'Navigational': navigational_matches * 2     # Weight navigational moderately
    }
    
    # Special patterns
    if any(word.startswith('how') for word in words):
        scores['Informational'] += 2
    if 'vs' in keyword_lower or 'versus' in keyword_lower:
        scores['Commercial'] += 2
    if any(word in ['buy', 'purchase', 'order'] for word in words[:2]):  # Early position matters
        scores['Transactional'] += 2
    
    # Get the highest scoring intent
    primary_intent = max(scores, key=scores.get)
    
    # If all scores are 0, default based on keyword structure
    if scores[primary_intent] == 0:
        if len(words) >= 3 and ('how' in words[0] or 'what' in words[0]):
            return 'Informational'
        elif any(brand in keyword_lower for brand in ['google', 'facebook', 'amazon', 'microsoft']):
            return 'Navigational'
        else:
            return 'Informational'  # Default fallback
    
    return primary_intent

def score_commercial_intent(keyword: str) -> float:
    """Score commercial intent keywords (0-100) - now uses intent classification"""
    intent = classify_search_intent(keyword)
    
    if intent == 'Transactional':
        return 100.0  # Highest commercial value
    elif intent == 'Commercial':
        return 80.0   # High commercial value
    elif intent == 'Navigational':
        return 40.0   # Medium commercial value
    else:  # Informational
        return 20.0   # Lower commercial value (but still has some)

def multifactor_score(
    keyword: str,
    volume: float,
    competition: float,
    cpc: float,
    difficulty_mode: DifficultyMode = "medium",
    params: MultiFactorParams = MultiFactorParams()
) -> Dict[str, Any]:
    """
    Calculate multi-factor opportunity score (0-100) with dynamic difficulty profiles
    """
    
    # Get weights for selected difficulty mode
    weights = get_difficulty_weights(difficulty_mode)
    
    # Calculate component scores (all 0-100)
    volume_score = score_volume(volume, params)
    competition_score = score_competition(competition) 
    cpc_score = score_cpc(cpc, params)
    longtail_score = score_longtail(keyword)
    commercial_score = score_commercial_intent(keyword)
    
    # Apply weights and calculate final score
    final_score = (
        weights["volume"] * volume_score +
        weights["competition"] * competition_score +
        weights["cpc"] * cpc_score +
        weights["longtail"] * longtail_score +
        weights["commercial"] * commercial_score
    )
    
    # Determine opportunity level
    if final_score >= params.excellent_threshold:
        opportunity_level = "Excellent"
    elif final_score >= params.good_threshold:
        opportunity_level = "Good"  
    elif final_score >= params.moderate_threshold:
        opportunity_level = "Moderate"
    else:
        opportunity_level = "Difficult"
    
    # Check competition filter based on difficulty mode
    competition_filter_passed = True
    max_competition = {
        "easy": params.easy_max_competition,
        "medium": params.medium_max_competition, 
        "hard": params.hard_max_competition
    }[difficulty_mode]
    
    if competition > max_competition:
        competition_filter_passed = False
    
    # Determine quick win status
    quick_win_thresholds = {
        "easy": params.easy_quick_win_threshold,
        "medium": params.medium_quick_win_threshold,
        "hard": params.hard_quick_win_threshold
    }
    
    is_quick_win = (
        competition_filter_passed and 
        final_score >= quick_win_thresholds[difficulty_mode] and
        volume >= 50 and
        len((keyword or "").split()) >= 3  # Require long-tail for quick wins
    )
    
    return {
        "score": round(final_score, 1),
        "opportunity_level": opportunity_level,
        "is_quick_win": is_quick_win,
        "difficulty_mode": difficulty_mode,
        "competition_filter_passed": competition_filter_passed,
        "components": {
            "volume_score": round(volume_score, 1),
            "competition_score": round(competition_score, 1),
            "cpc_score": round(cpc_score, 1),
            "longtail_score": round(longtail_score, 1),
            "commercial_score": round(commercial_score, 1)
        },
        "weights": weights,
        "raw_metrics": {
            "keyword": keyword,
            "volume": volume,
            "competition": competition,
            "cpc": cpc
        }
    }

# Old V2 functions removed - now using multi-factor scoring

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
    intent_badge: str = "Unknown"  # Intent classification badge with default

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
    difficulty_mode: DifficultyMode = "medium"  # New: Easy/Medium/Hard modes

class TargetAudience(BaseModel):
    primary: str
    secondary: str
    demographics: List[str]

class ContentStrategy(BaseModel):
    primary_goal: str
    content_type: str
    tone: str
    word_count: str

class ContentOutline(BaseModel):
    introduction: str
    main_sections: List[str]
    conclusion: str

class SEOOptimization(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str]
    meta_title: str
    meta_description: str

class CompetitiveAnalysis(BaseModel):
    top_competitors: List[str]
    content_gaps: List[str]
    differentiation_opportunities: List[str]

class ActionableInsights(BaseModel):
    quick_wins: List[str]
    long_term_strategies: List[str]
    content_calendar_suggestions: List[str]

class Brief(BaseModel):
    topic: str
    summary: str  # Keep for backward compatibility
    # Enhanced structured fields
    target_audience: Optional[TargetAudience] = None
    content_strategy: Optional[ContentStrategy] = None
    content_outline: Optional[ContentOutline] = None
    seo_optimization: Optional[SEOOptimization] = None
    competitive_analysis: Optional[CompetitiveAnalysis] = None
    actionable_insights: Optional[ActionableInsights] = None

class BriefRequest(BaseModel):
    keyword: str
    user_id: str
    user_plan: str = "free"
    variant: str = "a"
    use_serp_analysis: bool = True

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
        logger.error(f"Redis get error: {e}")
    return None

async def set_cache(key: str, data, expire_seconds: int = 3600):
    """Set data in Redis cache"""
    if not redis_client:
        return False
    
    try:
        await redis_client.setex(key, expire_seconds, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"Redis set error: {e}")
        return False

def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key"""
    key_data = ":".join(f"{k}={str(v).lower()}" for k, v in sorted(kwargs.items()) if v)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
    return f"{prefix}:{key_hash}"

# Enhanced keyword generation with SERP analysis
async def generate_keywords_with_serp(
    topic: str, 
    industry: str = "", 
    audience: str = "", 
    country: str = "US", 
    language: str = "en",
    max_results: int = 10,
    use_serp_analysis: bool = True,
    difficulty_mode: DifficultyMode = "medium"
) -> List[Keyword]:
    """Generate keywords enhanced with SERP analysis"""
    
    # Check cache first
    cache_key = generate_cache_key("keywords_serp", topic=topic, industry=industry, audience=audience, country=country)
    cached_data = await get_from_cache(cache_key)
    
    if cached_data:
        logger.info(f"🚀 Redis cache hit for SERP keywords: {topic}")
        keywords = []
        for item in cached_data:
            keywords.append(Keyword(**item))
        return keywords[:max_results]
    
    try:
        # Step 1: Generate initial keywords with OpenAI
        context = f"Industry: {industry or 'General'}, Audience: {audience or 'General public'}"
        
        prompt = f"""
Generate {max_results} RANKABLE keyword variations for the topic "{topic}". Focus on keywords that smaller websites can actually rank for.

Context: {context}

PRIORITIZE these types of rankable keywords:
1. Long-tail keywords (3+ words) - better for ranking
2. Intent-specific variations:
   - INFORMATIONAL: "how to", "what is", "guide to", "tutorial"
   - COMMERCIAL: "best", "top", "review", "vs", "comparison"  
   - TRANSACTIONAL: "buy", "cheap", "price", "deal", "under $X"
3. Problem-solving keywords: "fix", "solve", "troubleshoot"
4. Beginner-focused: "for beginners", "easy", "simple", "basic"
5. Year/seasonal: "2024", "2025", current trends
6. Branded alternatives (if applicable): "like [competitor]", "alternative to [brand]"

KEYWORD STRUCTURE EXAMPLES:
- "how to choose {topic} for beginners" (Informational)
- "best budget {topic} under $100" (Commercial)
- "buy {topic} online cheap" (Transactional)
- "{topic} vs [competitor] comparison" (Commercial)
- "free {topic} alternative to [brand]" (Commercial)

For each keyword, provide:
1. The keyword phrase (focus on long-tail, specific terms)
2. Monthly search volume (100-5000 range for rankability)
3. Estimated CPC in USD (higher CPC = more commercial value)
4. Competition level (0.0-0.6 for rankable keywords)
5. Mark as quick_win if competition < 0.4 AND volume > 100

AVOID these hard-to-rank keywords:
- Single broad terms
- High-competition commercial terms  
- Exact brand name searches

Format as JSON array:
[{{"keyword": "how to setup {topic} for beginners 2024", "volume": 800, "cpc": 1.20, "competition": 0.25, "is_quick_win": true}}]
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
        
        # Step 2: Enhance with SERP analysis if enabled
        for i, item in enumerate(keyword_data):
            keyword_text = item['keyword']
            
            # Get keyword metrics
            volume = item.get('volume', 0)
            competition = item.get('competition', 1.0)
            cpc = item.get('cpc', 0.0)
            
            # Calculate multi-factor score and classify intent
            score_result = multifactor_score(
                keyword=keyword_text,
                volume=volume,
                competition=competition,
                cpc=cpc,
                difficulty_mode=difficulty_mode
            )
            
            # Classify search intent for badge
            intent_badge = classify_search_intent(keyword_text)
            
            # Initialize keyword object
            keyword_obj = Keyword(
                keyword=keyword_text,
                volume=volume,
                cpc=cpc,
                competition=competition,
                opportunity_score=int(score_result["score"]),
                is_quick_win=score_result["is_quick_win"],
                serp_enhanced=False,
                intent_badge=intent_badge
            )
            
            # Enhance with SERP analysis for top keywords (limit API calls)
            if use_serp_analysis and i < 3:  # Only analyze top 3 to save API calls
                try:
                    logger.info(f"🔍 Analyzing SERP for: {keyword_text}")
                    serp_data = await serper_client.search(keyword_text, country, language)
                    
                    if serp_data:
                        # Analyze search intent
                        search_intent = serper_client.analyze_search_intent(keyword_text, serp_data)
                        
                        # Calculate difficulty score
                        difficulty_score = serper_client.calculate_difficulty_score(serp_data)
                        
                        # Update keyword with SERP data
                        keyword_obj.search_intent = search_intent
                        keyword_obj.difficulty_score = difficulty_score
                        keyword_obj.serp_enhanced = True
                        
                        # Recalculate using multi-factor scoring with SERP difficulty data
                        serp_competition = difficulty_score / 100.0  # Convert back to 0-1 scale
                        enhanced_result = multifactor_score(
                            keyword=keyword_text,
                            volume=volume,
                            competition=serp_competition,  # Use SERP difficulty
                            cpc=keyword_obj.cpc,
                            difficulty_mode=difficulty_mode
                        )
                        
                        keyword_obj.opportunity_score = int(enhanced_result["score"])
                        keyword_obj.is_quick_win = enhanced_result["is_quick_win"]
                        
                        logger.info(f"✅ SERP enhanced: {keyword_text} (difficulty: {difficulty_score}, intent: {search_intent})")
                
                except Exception as e:
                    logger.error(f"SERP analysis failed for {keyword_text}: {e}")
            
            keywords.append(keyword_obj)
        
        # Sort by enhanced opportunity score, then by quick wins
        keywords.sort(key=lambda k: (not k.is_quick_win, -k.opportunity_score))
        
        # Cache the results (2 hours for SERP-enhanced data)
        keywords_data = [k.dict() for k in keywords]
        await set_cache(cache_key, keywords_data, 7200)
        logger.info(f"✅ Cached SERP-enhanced keywords: {topic}")
        
        return keywords[:max_results]
        
    except Exception as e:
        logger.error(f"Error generating keywords: {e}")
        # Enhanced fallback keywords with intent variety and branded alternatives
        fallback_data = [
            {"keyword": f"how to choose {topic} for beginners", "volume": 800, "competition": 0.25, "cpc": 1.20},
            {"keyword": f"best budget {topic} under $100", "volume": 600, "competition": 0.20, "cpc": 0.90},
            {"keyword": f"{topic} vs alternatives comparison", "volume": 400, "competition": 0.35, "cpc": 1.80},
            {"keyword": f"buy cheap {topic} online", "volume": 500, "competition": 0.40, "cpc": 2.10},
            {"keyword": f"free {topic} alternative", "volume": 700, "competition": 0.30, "cpc": 0.60},
            {"keyword": f"what is the best {topic} 2024", "volume": 350, "competition": 0.45, "cpc": 1.50},
            {"keyword": f"{topic} tutorial for beginners", "volume": 450, "competition": 0.15, "cpc": 0.80},
        ]
        
        fallback_keywords = []
        for item in fallback_data:
            # Use multi-factor scoring for fallback keywords
            score_result = multifactor_score(
                keyword=item["keyword"],
                volume=item["volume"],
                competition=item["competition"],
                cpc=item["cpc"],
                difficulty_mode=difficulty_mode
            )
            
            # Classify intent for fallback keywords too
            intent_badge = classify_search_intent(item["keyword"])
            
            fallback_keywords.append(Keyword(
                keyword=item["keyword"],
                volume=item["volume"],
                cpc=item["cpc"],
                competition=item["competition"],
                opportunity_score=int(score_result["score"]),
                is_quick_win=score_result["is_quick_win"],
                serp_enhanced=False,
                intent_badge=intent_badge
            ))
        
        # Sort and return top results
        fallback_keywords.sort(key=lambda k: (not k.is_quick_win, -k.opportunity_score))
        return fallback_keywords

async def generate_brief_with_serp(keyword: str, country: str = "US", use_serp_analysis: bool = True) -> Brief:
    """Generate content brief enhanced with SERP analysis"""
    
    # Check cache first
    cache_key = generate_cache_key("brief_serp", keyword=keyword, country=country)
    cached_brief = await get_from_cache(cache_key)
    
    if cached_brief:
        logger.info(f"🚀 Redis cache hit for SERP brief: {keyword}")
        try:
            # Try to parse cached structured data
            cached_data = json.loads(cached_brief)
            return Brief(**cached_data)
        except:
            # If cache is old text format, regenerate
            pass

    try:
        serp_context = ""
        
        # Get SERP analysis if enabled
        if use_serp_analysis:
            try:
                logger.info(f"🔍 Analyzing SERP for brief: {keyword}")
                serp_data = await serper_client.search(keyword, country)
                
                if serp_data:
                    search_intent = serper_client.analyze_search_intent(keyword, serp_data)
                    organic_results = serp_data.get('organic', [])
                    
                    competitor_titles = [result.get('title', '') for result in organic_results[:3]]
                    
                    serp_context = f"""
SERP Analysis for "{keyword}":
- Search Intent: {search_intent}
- Top competing content: {', '.join(competitor_titles[:3])}
- Total organic results analyzed: {len(organic_results)}

Use this SERP data to create content that can outrank competitors.
"""
                    logger.info(f"✅ SERP context added for brief: {keyword}")
                
            except Exception as e:
                logger.error(f"SERP analysis failed for brief {keyword}: {e}")
        
        # Generate enhanced brief with structured JSON output
        prompt = f"""
Create a comprehensive content brief for the keyword "{keyword}".

{serp_context}

IMPORTANT: Return ONLY a valid JSON object with no additional text or explanation.

{{
  "target_audience": {{
    "primary": "Main target audience (e.g., 'Small business owners looking to improve their online presence')",
    "secondary": "Secondary audience (e.g., 'Marketing managers at mid-sized companies')",
    "demographics": ["Age group", "Professional level", "Industry/Interest"]
  }},
  "content_strategy": {{
    "primary_goal": "Main objective (e.g., 'Educate readers on best practices while positioning our solution')",
    "content_type": "Content format (e.g., 'comprehensive guide', 'comparison article', 'how-to tutorial')",
    "tone": "Writing style (e.g., 'professional yet approachable', 'authoritative expert', 'friendly conversational')",
    "word_count": "Target length (e.g., '2000-2500 words', '1500-2000 words')"
  }},
  "content_outline": {{
    "introduction": "What to cover in the opening (e.g., 'Hook with statistics, define the problem, preview solutions')",
    "main_sections": ["Specific H2 section 1", "Specific H2 section 2", "Specific H2 section 3", "Specific H2 section 4", "Specific H2 section 5"],
    "conclusion": "What to emphasize in closing (e.g., 'Summarize key takeaways, include call-to-action for next steps')"
  }},
  "seo_optimization": {{
    "primary_keyword": "{keyword}",
    "secondary_keywords": ["long-tail variation 1", "related term 2", "semantic keyword 3"],
    "meta_title": "SEO title 55-60 characters with primary keyword",
    "meta_description": "Compelling 150-160 character description that includes primary keyword and value proposition"
  }},
  "competitive_analysis": {{
    "top_competitors": ["domain1.com", "domain2.com", "domain3.com"],
    "content_gaps": ["Missing angle 1", "Underserved subtopic 2", "Opportunity area 3"],
    "differentiation_opportunities": ["Unique approach 1", "Better coverage of topic 2", "Stronger call-to-action 3"]
  }},
  "actionable_insights": {{
    "quick_wins": ["Immediate optimization 1", "Easy improvement 2", "Quick implementation 3"],
    "long_term_strategies": ["Strategic approach 1", "Advanced tactic 2", "Growth opportunity 3"],
    "content_calendar_suggestions": ["Follow-up article topic 1", "Related content idea 2", "Series continuation 3"]
  }}
}}

Make the content specific to "{keyword}" and actionable for content creators.
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert content strategist and SEO specialist. Always return valid JSON structure as requested."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            # Extract JSON from response (sometimes AI adds markdown formatting)
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '')
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '')
            
            structured_data = json.loads(ai_response.strip())
            
            # Create brief with structured data
            brief = Brief(
                topic=keyword,
                summary=f"Comprehensive content brief for '{keyword}' with structured analysis",
                target_audience=TargetAudience(**structured_data.get("target_audience", {})) if structured_data.get("target_audience") else None,
                content_strategy=ContentStrategy(**structured_data.get("content_strategy", {})) if structured_data.get("content_strategy") else None,
                content_outline=ContentOutline(**structured_data.get("content_outline", {})) if structured_data.get("content_outline") else None,
                seo_optimization=SEOOptimization(**structured_data.get("seo_optimization", {})) if structured_data.get("seo_optimization") else None,
                competitive_analysis=CompetitiveAnalysis(**structured_data.get("competitive_analysis", {})) if structured_data.get("competitive_analysis") else None,
                actionable_insights=ActionableInsights(**structured_data.get("actionable_insights", {})) if structured_data.get("actionable_insights") else None
            )
            
            # Cache the structured brief (4 hours for SERP-enhanced briefs)
            cache_data = brief.model_dump_json()
            await set_cache(cache_key, cache_data, 14400)
            logger.info(f"✅ Cached structured brief: {keyword}")
            
            return brief
            
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response for {keyword}: {je}")
            # Fallback to text-based brief
            brief = Brief(
                topic=keyword,
                summary=ai_response[:1000]  # Truncate if too long
            )
            return brief
        
    except Exception as e:
        logger.error(f"Error generating brief: {e}")
        # Return minimal fallback brief
        return Brief(
            topic=keyword,
            summary=f"## Content Brief: {keyword}\n\n### Target Audience\nPeople searching for \"{keyword}\" are looking for practical information.\n\n### Search Intent\nInformational - users want to learn about this topic.\n\n### Content Angle\nFocus on actionable advice with clear benefits."
        )# Routes
@app.get("/")
async def root():
    return {"message": "Quick Wins Finder API (SERP Enhanced - Simple)", "status": "running"}

@app.get("/health")
async def health_check():
    redis_connected = redis_client is not None
    if redis_connected:
        try:
            await redis_client.ping()
            redis_connected = True
        except:
            redis_connected = False
    
    serper_available = os.getenv("SERPER_API_KEY") is not None
    
    return {
        "ok": True,
        "redis_connected": redis_connected,
        "serper_available": serper_available,
        "serper_key_present": bool(os.getenv("SERPER_API_KEY")),
        "cache_strategy": "redis_serp_enhanced" if redis_connected else "no_cache"
    }

@app.post("/suggest-keywords/")
@limiter.limit("6/minute")  # Lower due to SERP API calls
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
            use_serp_analysis=keywords_request.use_serp_analysis,
            difficulty_mode=keywords_request.difficulty_mode
        )
        
        serp_enhanced_count = len([k for k in keywords if k.serp_enhanced])
        
        return {
            "keywords": [k.model_dump() for k in keywords],
            "total": len(keywords),
            "quick_wins": len([k for k in keywords if k.is_quick_win]),
            "serp_enhanced": serp_enhanced_count,
            "cached": True if redis_client else False
        }
        
    except Exception as e:
        logger.error(f"Error in suggest_keywords: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate keywords")

@app.post("/generate-brief/")
@limiter.limit("3/minute")  # Lower due to SERP API calls
async def generate_content_brief(request: Request, brief_request: BriefRequest):
    """Generate content brief with optional SERP enhancement"""
    
    if not brief_request.keyword.strip():
        raise HTTPException(status_code=400, detail="Keyword is required")
    
    try:
        brief = await generate_brief_with_serp(
            brief_request.keyword,
            country="US",
            use_serp_analysis=brief_request.use_serp_analysis
        )
        
        return {
            "brief": brief.model_dump(),
            "serp_enhanced": brief_request.use_serp_analysis,
            "cached": True if redis_client else False
        }
        
    except Exception as e:
        logger.error(f"Error in generate_brief: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate brief")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
