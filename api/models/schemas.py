# api/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal, Dict

class Plan(BaseModel):
    # Use Literal for strict allowed values to avoid Field(pattern) compatibility issues across Pydantic versions
    user_plan: Literal["free", "paid"] = "free"

class WithUser(BaseModel):
    # Temporary identity until auth is added
    user_id: str = "dev-user"

class GenerateBriefRequest(Plan, WithUser):
    keyword: str
    variant: Optional[str] = "a"  # "a" or "b" for different brief variations

# Brief-specific models for structured data
class OutlineItem(BaseModel):
    heading: str
    description: str

class FAQItem(BaseModel):
    question: str
    answer: str

class WordCountEstimate(BaseModel):
    min_words: int
    max_words: int
    target_words: int
    reasoning: str

class BacklinkOpportunity(BaseModel):
    category: str
    websites: List[str]
    reason: str
    difficulty: Literal["Easy", "Medium", "Hard"]

class ContentBrief(BaseModel):
    target_reader: str
    search_intent: str
    angle: str
    outline: List[OutlineItem]
    key_entities: List[str]
    faqs: List[FAQItem]
    checklist: List[str]
    meta_title: str
    meta_description: str
    # New heuristics-based fields
    recommended_word_count: Optional[WordCountEstimate] = None
    backlink_opportunities: Optional[List[BacklinkOpportunity]] = None

class GenerateBriefResponse(BaseModel):
    brief: ContentBrief  # Now uses structured ContentBrief model
    meta: Optional[dict] = None

class SerpRequest(Plan, WithUser):
    keyword: str
    country: Optional[str] = "US"
    language: Optional[str] = "en"

class SerpResponse(BaseModel):
    serp: Any  # keep loose for now; later define structure
    analysis: Optional[dict] = None  # competitive analysis for paid plans
    meta: Optional[dict] = None

class SuggestKeywordsRequest(Plan, WithUser):
    topic: str
    max_results: int = 20
    industry: Optional[str] = None
    audience: Optional[str] = None
    country: Optional[str] = "US"
    language: Optional[str] = "en"

class KeywordItem(BaseModel):
    keyword: str
    volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[float] = None
    source: str = "GKP"
    # Optional extras to improve UX without breaking existing clients
    opportunity_score: Optional[float] = None  # Changed from int to float
    is_quick_win: Optional[bool] = None

class ClusterKeyword(BaseModel):
    keyword: str
    reason: Optional[str] = None

class ClusterGroup(BaseModel):
    name: str                      # e.g., "Commercial / Buyer intent"
    intent: str                    # informational | commercial | navigational
    keywords: List[ClusterKeyword] # small curated list (5–10)

class SuggestKeywordsResponse(BaseModel):
    keywords: List[KeywordItem]
    clusters: Optional[List[ClusterGroup]] = None
    quick_wins: Optional[List[KeywordItem]] = None  # Changed from List[str] to List[KeywordItem]
    notes: Optional[str] = None
    meta: Optional[dict] = None

class SuggestionsRequest(BaseModel):
    brief: str
    serp: Any

class SuggestionsResponse(BaseModel):
    ideas: List[str]

class ProductDescriptionRequest(Plan, WithUser):
    product_name: str
    features: List[str]
    channel: Optional[str] = "ecommerce"   # ecommerce | amazon | etsy
    tone: Optional[str] = "neutral"
    length: Optional[str] = "medium"       # short | medium | long

class ProductDescriptionResponse(BaseModel):
    title: str
    bullets: List[str]
    description: str
    seo_keywords: List[str]
    notes: Optional[str] = None
    meta: Optional[dict] = None
