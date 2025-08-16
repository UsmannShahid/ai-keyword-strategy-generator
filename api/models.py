# api/models.py
# Models for the AI Keyword Strategy Tool API

# api/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class KeywordRow(BaseModel):
    keyword: str = Field(..., alias="Keyword")
    intent: Optional[str] = Field(None, alias="Intent")
    qw_score: float = Field(..., alias="QW Score")
    volume: Optional[int] = Field(None, alias="Volume")
    notes: Optional[str] = Field(None, alias="Notes")

class KeywordResponse(BaseModel):
    items: List[KeywordRow]
    seed: str
    country: str
    language: str

class Brief(BaseModel):
    title: str
    meta_description: str
    outline: Dict[str, Any]
    related_keywords: List[str] = []
    suggested_word_count: Optional[int] = None
    content_type: Optional[str] = None
    internal_link_ideas: List[str] = []
    external_link_ideas: List[str] = []
    faqs: List[Dict[str, str]] = []

class WriterNotes(BaseModel):
    target_audience: Optional[str] = None
    search_intent: Optional[str] = None
    primary_angle: Optional[str] = None
    writer_notes: List[str] = []
    must_cover_sections: List[str] = []
    entity_gaps: List[str] = []
    data_freshness: List[str] = []
    internal_link_targets: List[str] = []
    external_citations_needed: List[str] = []
    formatting_enhancements: List[str] = []
    tone_style: List[str] = []
    cta_ideas: List[str] = []
    risk_flags: List[str] = []
    recommended_word_count: Optional[int] = None

