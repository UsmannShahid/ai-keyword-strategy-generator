# api/core/heuristics.py
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class WordCountEstimate:
    min_words: int
    max_words: int
    target_words: int
    reasoning: str

@dataclass
class BacklinkBucket:
    category: str
    websites: List[str]
    reason: str
    difficulty: str  # "Easy", "Medium", "Hard"

def estimate_word_count(keyword: str, search_intent: str = "informational", competition_level: str = "medium") -> WordCountEstimate:
    """
    Estimate optimal word count based on keyword characteristics and competition.
    
    Args:
        keyword: Target keyword
        search_intent: "informational", "commercial", "navigational", "transactional"
        competition_level: "low", "medium", "high"
    
    Returns:
        WordCountEstimate with min, max, target word counts and reasoning
    """
    base_words = 1500  # Default baseline
    
    # Adjust based on search intent
    intent_multipliers = {
        "informational": 1.3,   # Comprehensive guides need more content
        "commercial": 1.0,      # Product comparisons are moderate length
        "transactional": 0.7,   # Purchase pages are typically shorter
        "navigational": 0.5     # Brand/specific site pages are brief
    }
    
    # Adjust based on competition level
    competition_multipliers = {
        "low": 0.8,     # Less content needed to rank
        "medium": 1.0,  # Standard content length
        "high": 1.4     # Need comprehensive content to compete
    }
    
    # Keyword-specific adjustments
    keyword_lower = keyword.lower()
    
    # Technical/complex topics need more words
    if any(term in keyword_lower for term in ["how to", "guide", "tutorial", "setup", "install", "configure"]):
        base_words *= 1.4
        
    # Comparison keywords need moderate length
    elif any(term in keyword_lower for term in ["vs", "versus", "compare", "comparison", "best", "top"]):
        base_words *= 1.1
        
    # Quick answer keywords can be shorter
    elif any(term in keyword_lower for term in ["what is", "definition", "meaning", "price", "cost"]):
        base_words *= 0.8
        
    # Commercial/buying intent keywords are moderate
    elif any(term in keyword_lower for term in ["buy", "purchase", "price", "cost", "cheap", "discount"]):
        base_words *= 0.9
    
    # Apply multipliers
    intent_multiplier = intent_multipliers.get(search_intent.lower(), 1.0)
    competition_multiplier = competition_multipliers.get(competition_level.lower(), 1.0)
    
    target_words = int(base_words * intent_multiplier * competition_multiplier)
    
    # Set reasonable bounds (20% range around target)
    min_words = max(300, int(target_words * 0.8))
    max_words = min(5000, int(target_words * 1.2))
    
    # Generate reasoning
    reasoning_parts = []
    if intent_multiplier > 1.0:
        reasoning_parts.append(f"{search_intent} content typically requires comprehensive coverage")
    if competition_multiplier > 1.0:
        reasoning_parts.append(f"{competition_level} competition demands thorough content")
    if "how to" in keyword_lower or "guide" in keyword_lower:
        reasoning_parts.append("tutorial content needs step-by-step detail")
    
    reasoning = "; ".join(reasoning_parts) if reasoning_parts else "standard content length for keyword type"
    
    return WordCountEstimate(
        min_words=min_words,
        max_words=max_words,
        target_words=target_words,
        reasoning=reasoning
    )

def recommend_backlink_buckets(keyword: str, industry: str = "general", target_reader: str = "") -> List[BacklinkBucket]:
    """
    Recommend categorized backlink opportunities based on keyword and context.
    
    Args:
        keyword: Target keyword
        industry: Industry vertical (e.g., "tech", "health", "finance", "ecommerce")
        target_reader: Description of target audience
    
    Returns:
        List of BacklinkBucket objects with categorized link opportunities
    """
    buckets = []
    keyword_lower = keyword.lower()
    industry_lower = industry.lower()
    
    # Industry-specific directories and resources
    if industry_lower in ["tech", "software", "saas"]:
        buckets.append(BacklinkBucket(
            category="Tech Directories",
            websites=["ProductHunt", "G2", "Capterra", "Stack Overflow", "GitHub", "Dev.to"],
            reason="High authority in tech space with relevant audiences",
            difficulty="Medium"
        ))
    elif industry_lower in ["health", "medical", "wellness"]:
        buckets.append(BacklinkBucket(
            category="Health Resources", 
            websites=["Healthline", "WebMD", "Medical News Today", "PubMed", "Mayo Clinic"],
            reason="Authoritative health sources for credible backlinks",
            difficulty="Hard"
        ))
    elif industry_lower in ["finance", "fintech", "investing"]:
        buckets.append(BacklinkBucket(
            category="Financial Publications",
            websites=["Investopedia", "Forbes", "MarketWatch", "Financial Times", "Bloomberg"],
            reason="High authority financial content sites",
            difficulty="Hard"
        ))
    elif industry_lower in ["ecommerce", "retail", "shopping"]:
        buckets.append(BacklinkBucket(
            category="Ecommerce Resources",
            websites=["Shopify Blog", "BigCommerce", "Ecommerce Times", "Practical Ecommerce"],
            reason="Industry-specific publications for ecommerce",
            difficulty="Medium"
        ))
    
    # Universal high-value opportunities
    buckets.extend([
        BacklinkBucket(
            category="News & Media",
            websites=["Help a Reporter Out (HARO)", "ProfNet", "SourceBottle", "Qwoted"],
            reason="PR opportunities for expert quotes and mentions",
            difficulty="Medium"
        ),
        BacklinkBucket(
            category="Educational Resources",
            websites=["Wikipedia", "Educational blogs", "University resources", "Research papers"],
            reason="High authority educational content linking opportunities",
            difficulty="Hard"
        ),
        BacklinkBucket(
            category="Industry Forums",
            websites=["Reddit", "Quora", "Industry forums", "Professional communities"],
            reason="Community engagement and thought leadership opportunities",
            difficulty="Easy"
        )
    ])
    
    # Content-type specific opportunities
    if any(term in keyword_lower for term in ["how to", "guide", "tutorial"]):
        buckets.append(BacklinkBucket(
            category="Tutorial Resources",
            websites=["Instructables", "WikiHow", "Udemy", "YouTube", "Tutorial sites"],
            reason="Natural fit for educational/how-to content",
            difficulty="Easy"
        ))
        
    if any(term in keyword_lower for term in ["tool", "software", "app"]):
        buckets.append(BacklinkBucket(
            category="Tool Directories",
            websites=["Product Hunt", "Alternative.to", "Tool directories", "Review sites"],
            reason="Tool-specific directories and comparison sites",
            difficulty="Medium"
        ))
        
    if any(term in keyword_lower for term in ["best", "top", "review", "comparison"]):
        buckets.append(BacklinkBucket(
            category="Review Sites",
            websites=["Review platforms", "Comparison sites", "Listicle publications"],
            reason="Natural placement in comparison and review content",
            difficulty="Medium"
        ))
    
    # Local/geographic opportunities
    if any(term in keyword_lower for term in ["near me", "local", "city", "location"]):
        buckets.append(BacklinkBucket(
            category="Local Resources",
            websites=["Local directories", "Chamber of Commerce", "City websites", "Local news"],
            reason="Geographic relevance for local search optimization",
            difficulty="Easy"
        ))
    
    # B2B vs B2C targeting
    if "business" in target_reader.lower() or "b2b" in target_reader.lower():
        buckets.append(BacklinkBucket(
            category="B2B Publications",
            websites=["Harvard Business Review", "Inc.com", "Entrepreneur", "Industry trade pubs"],
            reason="B2B audience alignment for business-focused content",
            difficulty="Hard"
        ))
    elif "consumer" in target_reader.lower() or "personal" in target_reader.lower():
        buckets.append(BacklinkBucket(
            category="Consumer Media",
            websites=["Lifestyle blogs", "Consumer magazines", "Personal finance sites"],
            reason="Consumer-focused publications for individual users",
            difficulty="Medium"
        ))
    
    # Remove duplicates and limit to top 6 most relevant buckets
    seen_categories = set()
    unique_buckets = []
    for bucket in buckets:
        if bucket.category not in seen_categories:
            seen_categories.add(bucket.category)
            unique_buckets.append(bucket)
            if len(unique_buckets) >= 6:
                break
    
    return unique_buckets

def analyze_keyword_characteristics(keyword: str) -> Dict[str, any]:
    """
    Analyze keyword to extract characteristics for heuristic calculations.
    
    Args:
        keyword: Target keyword to analyze
        
    Returns:
        Dictionary with keyword characteristics
    """
    keyword_lower = keyword.lower()
    word_count = len(keyword.split())
    
    # Detect intent signals
    intent_signals = {
        "informational": ["what", "how", "why", "guide", "tutorial", "learn", "understand"],
        "commercial": ["best", "top", "review", "compare", "vs", "versus", "alternative"],
        "transactional": ["buy", "purchase", "order", "price", "cost", "cheap", "discount"],
        "navigational": ["login", "sign in", "website", "official", "homepage"]
    }
    
    detected_intent = "informational"  # default
    for intent, signals in intent_signals.items():
        if any(signal in keyword_lower for signal in signals):
            detected_intent = intent
            break
    
    # Detect complexity indicators
    complexity_indicators = {
        "high": ["enterprise", "professional", "advanced", "expert", "complex"],
        "medium": ["business", "intermediate", "standard", "regular"],
        "low": ["simple", "basic", "easy", "beginner", "quick"]
    }
    
    detected_complexity = "medium"  # default
    for complexity, indicators in complexity_indicators.items():
        if any(indicator in keyword_lower for indicator in indicators):
            detected_complexity = complexity
            break
    
    return {
        "word_count": word_count,
        "estimated_intent": detected_intent,
        "complexity": detected_complexity,
        "is_long_tail": word_count >= 3,
        "is_branded": any(brand in keyword_lower for brand in ["google", "microsoft", "apple", "amazon"]),
        "is_local": any(local in keyword_lower for local in ["near me", "local", "nearby"]),
        "is_question": keyword_lower.startswith(("what", "how", "why", "when", "where", "which")),
        "is_comparison": any(comp in keyword_lower for comp in ["vs", "versus", "compare", "best", "top"])
    }