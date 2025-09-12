# api/routes/brief.py
from fastapi import APIRouter, HTTPException
from ..models.schemas import (
    GenerateBriefRequest, 
    GenerateBriefResponse, 
    ContentBrief,
    OutlineItem,
    FAQItem,
    WordCountEstimate,
    BacklinkOpportunity
)
from ..core.config import get_settings
from ..core.gpt import generate_brief
from ..core.heuristics import estimate_word_count, recommend_backlink_buckets, analyze_keyword_characteristics
from api.core.usage import consume_quota
from src.analytics import log_event, timed
from ..db import get_brief_cache, set_brief_cache, init_brief_cache_table
from typing import Dict, Any, List
import json

router = APIRouter(tags=["brief"])

def _validate_and_structure_brief(brief_data: Dict[str, Any], keyword: str) -> ContentBrief:
    """Validate and structure LLM output into ContentBrief model."""
    try:
        # Ensure outline is properly structured
        outline = brief_data.get("outline", [])
        structured_outline = []
        for item in outline:
            if isinstance(item, dict) and "heading" in item:
                structured_outline.append(OutlineItem(**item))
            elif isinstance(item, str):
                # Convert string to structured format
                structured_outline.append(OutlineItem(heading=item, description=f"Details about {item.lower()}"))
            else:
                # Fallback for unexpected format
                structured_outline.append(OutlineItem(heading=str(item), description=f"Information about {item}"))
        # If no outline was provided or it was empty, provide a sensible default
        if not structured_outline:
            structured_outline = [
                OutlineItem(heading="Introduction", description=f"Overview of {keyword}"),
                OutlineItem(heading="Key Points", description=f"Essential aspects of {keyword}"),
                OutlineItem(heading="How To", description=f"Practical steps related to {keyword}"),
                OutlineItem(heading="Conclusion", description=f"Summary and next steps for {keyword}")
            ]

        # Ensure FAQs are properly structured
        faqs = brief_data.get("faqs", [])
        structured_faqs = []
        for faq in faqs:
            if isinstance(faq, dict):
                if "question" in faq and "answer" in faq:
                    structured_faqs.append(FAQItem(**faq))
                elif "q" in faq and "a" in faq:
                    structured_faqs.append(FAQItem(question=faq["q"], answer=faq["a"]))
            elif isinstance(faq, str):
                # Convert string to Q&A format
                structured_faqs.append(FAQItem(
                    question=f"What about {faq}?",
                    answer=f"Information about {faq} will be provided."
                ))
        
        # Create ContentBrief with validated data
        return ContentBrief(
            target_reader=brief_data.get("target_reader", f"Audience interested in {keyword}"),
            search_intent=brief_data.get("search_intent", "informational"),
            angle=brief_data.get("angle", f"Comprehensive guide to {keyword}"),
            outline=structured_outline,
            key_entities=brief_data.get("key_entities", [keyword]),
            faqs=structured_faqs,
            checklist=brief_data.get("checklist", ["Include target keyword", "Add images", "Optimize meta tags"]),
            meta_title=brief_data.get("meta_title", f"{keyword}: Complete Guide")[:60],
            meta_description=brief_data.get("meta_description", f"Learn about {keyword} with our comprehensive guide.")[:160]
        )
    except Exception as e:
        # Fallback with natural, helpful structure
        return ContentBrief(
            target_reader=f"Anyone curious about {keyword} who wants clear, practical information",
            search_intent="informational",
            angle=f"A straightforward, helpful guide to understanding {keyword}",
            outline=[
                OutlineItem(heading="What You Need to Know", description=f"The essentials about {keyword} explained simply"),
                OutlineItem(heading="Why This Matters", description=f"Real reasons people care about {keyword}"),
                OutlineItem(heading="Your Options", description=f"Different ways to approach {keyword}"),
                OutlineItem(heading="Making It Work for You", description=f"How to get the most out of {keyword}")
            ],
            key_entities=[keyword.title()],
            faqs=[FAQItem(question=f"What exactly is {keyword}?", answer="We'll break this down in simple terms with real examples.")],
            checklist=["Write naturally and conversationally", "Include helpful examples", "Add useful links and resources", "Make sure it's easy to scan", "Focus on what readers actually need"],
            meta_title=f"{keyword.title()}: Clear, Practical Guide",
            meta_description=f"Get the info you need about {keyword}. Clear explanations, practical advice, no complicated jargon."
        )

@router.post("/", response_model=GenerateBriefResponse)
def create_brief(payload: GenerateBriefRequest):
    # Initialize cache table if not exists
    init_brief_cache_table()
    
    # Check cache first
    cached_result = get_brief_cache(payload.keyword, payload.variant)
    if cached_result:
        # Return cached result without consuming quota
        try:
            cached_brief = ContentBrief(**cached_result["brief"])
            return GenerateBriefResponse(
                brief=cached_brief,
                meta={"from_cache": True, "cached_at": cached_result["cached_at"]},
            )
        except Exception:
            # If cached data is corrupted, proceed with fresh generation
            pass
    
    settings = get_settings(payload.user_plan)

    # Atomically consume quota before doing any work
    success, remaining = consume_quota(payload.user_id, payload.user_plan, "brief_create", 1)
    if not success:
        raise HTTPException(status_code=402, detail="Brief quota exceeded. Upgrade or wait until next month.")

    event_type = "brief_create"
    endpoint = "/generate-brief"

    try:
        with timed() as t:
            # Generate brief from LLM
            brief_data = generate_brief(payload.keyword, model=settings["gpt_model"], variant=payload.variant)
            if not brief_data:
                raise HTTPException(status_code=502, detail="Empty brief from model")
            
            # Validate and structure the brief
            structured_brief = _validate_and_structure_brief(brief_data, payload.keyword)
            
            # Analyze keyword characteristics for heuristics
            keyword_analysis = analyze_keyword_characteristics(payload.keyword)
            
            # Generate word count estimate using heuristics
            word_count_estimate = estimate_word_count(
                payload.keyword,
                search_intent=structured_brief.search_intent,
                competition_level="medium"  # Default; could be enhanced with SERP data
            )
            
            # Generate backlink opportunities using heuristics
            backlink_buckets = recommend_backlink_buckets(
                payload.keyword,
                industry="general",  # Could be enhanced by analyzing key_entities
                target_reader=structured_brief.target_reader
            )
            
            # Convert heuristics data to Pydantic models
            structured_word_count = WordCountEstimate(
                min_words=word_count_estimate.min_words,
                max_words=word_count_estimate.max_words,
                target_words=word_count_estimate.target_words,
                reasoning=word_count_estimate.reasoning
            )
            
            structured_backlinks = [
                BacklinkOpportunity(
                    category=bucket.category,
                    websites=bucket.websites,
                    reason=bucket.reason,
                    difficulty=bucket.difficulty
                ) for bucket in backlink_buckets
            ]
            
            # Add heuristics to the structured brief
            structured_brief.recommended_word_count = structured_word_count
            structured_brief.backlink_opportunities = structured_backlinks
            
            # Cache the complete brief for future requests
            try:
                set_brief_cache(payload.keyword, payload.variant, structured_brief.model_dump())
            except Exception:
                # Cache failure shouldn't break the request
                pass
            
        # No need to log_usage here - already done atomically in consume_quota
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            latency_ms=t.elapsed_ms,
            success=True,
        )
        return GenerateBriefResponse(
            brief=structured_brief,
            meta={"remaining": {"brief_create": remaining}},
        )
    except HTTPException:
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            success=False,
            error="HTTPException",
        )
        raise
    except Exception as e:
        # Don't leak internals to client; log briefly and return generic message.
        log_event(
            user_id=payload.user_id,
            plan=payload.user_plan,
            event_type=event_type,
            endpoint=endpoint,
            keyword=payload.keyword,
            success=False,
            error=str(e)[:2000],
        )
        detail = "Missing OPENAI_API_KEY" if "OPENAI_API_KEY" in str(e) else "Brief generation failed"
        raise HTTPException(status_code=500, detail=detail)
