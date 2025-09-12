#!/usr/bin/env python3
"""
Simple Free Version API Server
Minimal dependencies version for testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import openai
import json

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="Quick Wins Finder API (Simple)",
    description="Simplified API for testing",
    version="1.0.0"
)

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
    user_id: str = "test"
    user_plan: str = "free"
    # Optional fields that frontend might send
    max_results: Optional[int] = 10
    industry: Optional[str] = None
    audience: Optional[str] = None
    country: Optional[str] = "us"
    difficulty_mode: Optional[str] = "medium"

@app.get("/")
def root():
    return {"message": "Quick Wins Finder API (Simple)", "status": "running"}

@app.post("/suggest-keywords/")
async def suggest_keywords(request: KeywordRequest):
    """Generate keyword suggestions"""
    
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        prompt = f"""
Generate 10 keyword variations for the topic "{request.topic}".

For each keyword, provide:
1. The keyword phrase  
2. Estimated monthly search volume (realistic numbers, 100-5000 range)
3. Estimated CPC in USD (0.50-3.00 range)
4. Competition level (0.0-1.0, where 0 = no competition, 1 = maximum competition)
5. Whether it's a "quick win" (use criteria below)

Quick Win Criteria (aim for 50-60% quick wins):
- Competition ≤ 0.5 (50%)
- Volume ≥ 50 (minimum viable volume)
- CPC ≥ 0.5 (indicates some commercial value)
- Prefer 3+ word phrases (long-tail advantage)
- Include modifiers: "best", "cheap", "affordable", "for beginners", "easy", "simple", "under $X", "vs", "review", "tools", "free"

Format as JSON array:
[{{"keyword": "example keyword", "volume": 1200, "cpc": 1.50, "competition": 0.3, "is_quick_win": true}}]
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
            # Enhanced opportunity scoring
            volume = item.get('volume', 0)
            competition = item.get('competition', 1.0)
            cpc = item.get('cpc', 0.0)
            keyword_text = item.get('keyword', '')
            is_quick_win = item.get('is_quick_win', False)
            
            # Simple but effective opportunity score (0-100)
            volume_score = min(40, (volume / 1000) * 40) if volume > 0 else 0
            competition_score = (1 - competition) * 30
            cpc_score = min(15, (cpc / 3.0) * 15) if cpc > 0 else 5
            
            # Long-tail bonus
            word_count = len(keyword_text.split())
            longtail_bonus = min(10, max(0, (word_count - 2) * 3))
            
            # Intent bonus
            intent_words = ['best', 'cheap', 'affordable', 'guide', 'how to', 'tips', 'tools', 
                          'review', 'vs', 'under', 'for beginners', 'easy', 'simple', 'free']
            intent_bonus = 5 if any(word.lower() in keyword_text.lower() for word in intent_words) else 0
            
            opportunity_score = int(min(100, max(0, 
                volume_score + competition_score + cpc_score + longtail_bonus + intent_bonus
            )))
            
            # Enhanced quick win detection
            enhanced_quick_win = (
                is_quick_win or  
                (competition <= 0.5 and volume >= 50 and opportunity_score >= 45) or
                (competition <= 0.3 and volume >= 30 and opportunity_score >= 35)
            )
            
            keywords.append(Keyword(
                keyword=keyword_text,
                volume=volume,
                cpc=cpc,
                competition=competition,
                opportunity_score=opportunity_score,
                is_quick_win=enhanced_quick_win
            ))
        
        # Sort by quick wins first, then by opportunity score
        keywords.sort(key=lambda k: (not k.is_quick_win, -k.opportunity_score))
        
        quick_wins_count = len([k for k in keywords if k.is_quick_win])
        
        return {
            "keywords": [k.dict() for k in keywords],
            "total": len(keywords),
            "quick_wins": quick_wins_count,
            "serp_enhanced": 0,
            "cached": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")

class BriefRequest(BaseModel):
    keyword: str
    user_id: str = "test"

@app.post("/generate-brief/")
async def generate_brief(request: BriefRequest):
    """Generate content brief for a keyword"""
    
    if not openai.api_key:
        # Fallback for when no OpenAI key is available
        return {
            "brief": {
                "topic": request.keyword,
                "summary": f"Content brief for '{request.keyword}' - This is a placeholder brief for the free version. You can expand this with detailed content strategy, target audience analysis, competitive insights, and content structure recommendations."
            },
            "cached": False
        }
    
    try:
        prompt = f"""
You are an SEO strategist. Create a content brief for "{request.keyword}" in a clear, human-readable format.

Rules:
- Output must look like a content plan/strategy document
- Use numbered sections, short paragraphs, and bullet points
- No filler phrases like "comprehensive overview" or "make informed decisions"
- Every section must have actionable notes for the content writer
- Each H2/H3 should include a word count target + bullet points on what to cover
- Include SEO strategy (primary keyword, related keywords, snippet targets)
- Include content gaps and competitive insights
- End with goals, CTAs, and success metrics

Format exactly like this:

Content Overview
Topic: [topic]
Content Type: [blog post/guide/tutorial]
Word Count: ~[number]

Target Audience
[demographic], [interest/profession]
Pain Points: [specific problems they face]
Search Intent: [what they want to accomplish]

Suggested Headline
"[compelling headline that includes keyword naturally]"

Content Structure
H2: [section title] ([word count] words)
• [what to cover - specific bullets]
• [actionable guidance for writer]

H2: [next section] ([word count] words)
• [specific points to address]
• [examples or data to include]

[Continue with 4-6 H2 sections total]

SEO Strategy
Primary Keyword: {request.keyword}
Related Keywords: [3-5 related terms]
Snippet Targets: "[question]", "[another question]"

Content Gaps & Competitive Insights
[what's missing from current content on this topic]
[opportunity for differentiation]

CTA & Success Metrics
CTA: [specific call to action]
Metrics: [measurable outcomes to track]

Meta Info
Title: [SEO title under 60 chars]
Meta Description: [compelling description under 160 chars]

Make this specific and actionable - not generic advice.
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SEO strategist who creates practical content briefs. Write in a clear, structured format with specific word counts, actionable bullets, and no fluff. Focus on what content writers actually need to create great content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content_brief = response.choices[0].message.content.strip()
        
        return {
            "brief": {
                "topic": request.keyword,
                "summary": content_brief
            },
            "cached": False
        }
        
    except Exception as e:
        # Fallback in case of API errors
        return {
            "brief": {
                "topic": request.keyword,
                "summary": f"""# Content Brief: {request.keyword}

## Content Overview
Create a comprehensive guide about {request.keyword} that addresses the key questions and needs of your target audience.

## Target Audience
- People searching for information about {request.keyword}
- Beginners to intermediate level users
- Those looking for practical, actionable advice

## Suggested Content Structure
1. **Introduction** - What is {request.keyword} and why it matters
2. **Main Benefits** - Key advantages and value propositions
3. **Step-by-Step Guide** - Practical implementation advice
4. **Best Practices** - Tips and recommendations
5. **Common Mistakes** - What to avoid
6. **Conclusion** - Summary and next steps

## SEO Strategy
- Primary keyword: {request.keyword}
- Include variations and related terms naturally
- Aim for 1,500-2,500 words for comprehensive coverage
- Use clear headings and bullet points for readability

## Content Goals
- Educate readers about {request.keyword}
- Provide actionable insights they can implement
- Build authority and trust in the topic area
- Encourage engagement and sharing

*This is a basic brief template. For more detailed, AI-generated briefs, ensure your OpenAI API key is properly configured.*"""
            },
            "cached": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
