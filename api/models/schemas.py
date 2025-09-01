# api/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Literal

class Plan(BaseModel):
    # Use Literal for strict allowed values to avoid Field(pattern) compatibility issues across Pydantic versions
    user_plan: Literal["free", "paid"] = "free"

class GenerateBriefRequest(Plan):
    keyword: str

class GenerateBriefResponse(BaseModel):
    brief: str

class SerpRequest(Plan):
    keyword: str

class SerpResponse(BaseModel):
    serp: Any  # keep loose for now; later define structure

class SuggestKeywordsRequest(Plan):
    topic: str
    max_results: int = 20

class KeywordItem(BaseModel):
    keyword: str
    volume: Optional[int] = None
    cpc: Optional[float] = None
    competition: Optional[float] = None
    source: str = "GKP"

class SuggestKeywordsResponse(BaseModel):
    keywords: List[KeywordItem]
    clustered_markdown: Optional[str] = None  # for paid users later

class SuggestionsRequest(BaseModel):
    brief: str
    serp: Any

class SuggestionsResponse(BaseModel):
    ideas: List[str]
