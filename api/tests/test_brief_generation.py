# api/tests/test_brief_generation.py
import pytest
from unittest.mock import Mock, patch
from api.models.schemas import (
    ContentBrief, 
    OutlineItem, 
    FAQItem, 
    WordCountEstimate, 
    BacklinkOpportunity,
    GenerateBriefRequest
)
from api.routes.brief import _validate_and_structure_brief
from api.core.heuristics import estimate_word_count, recommend_backlink_buckets


class TestBriefStructureValidation:
    """Test brief data validation and structuring."""
    
    def test_valid_brief_structure(self):
        """Test processing of properly structured brief data."""
        brief_data = {
            "target_reader": "Python developers",
            "search_intent": "informational",
            "angle": "Comprehensive guide to FastAPI",
            "outline": [
                {"heading": "Introduction", "description": "Overview of FastAPI"},
                {"heading": "Installation", "description": "How to install FastAPI"}
            ],
            "key_entities": ["FastAPI", "Python", "REST API"],
            "faqs": [
                {"question": "What is FastAPI?", "answer": "FastAPI is a modern web framework"}
            ],
            "checklist": ["Install Python", "Create virtual environment"],
            "meta_title": "FastAPI Complete Guide",
            "meta_description": "Learn FastAPI with this comprehensive guide"
        }
        
        result = _validate_and_structure_brief(brief_data, "fastapi tutorial")
        
        assert isinstance(result, ContentBrief)
        assert result.target_reader == "Python developers"
        assert result.search_intent == "informational"
        assert len(result.outline) == 2
        assert all(isinstance(item, OutlineItem) for item in result.outline)
        assert len(result.faqs) == 1
        assert all(isinstance(item, FAQItem) for item in result.faqs)
    
    def test_brief_with_string_outline(self):
        """Test conversion of string outline items to structured format."""
        brief_data = {
            "target_reader": "Developers",
            "search_intent": "informational",
            "angle": "Learning guide",
            "outline": ["Introduction", "Setup", "Advanced Topics"],
            "key_entities": ["Python"],
            "faqs": [],
            "checklist": ["Step 1"],
            "meta_title": "Guide",
            "meta_description": "Description"
        }
        
        result = _validate_and_structure_brief(brief_data, "python")
        
        assert len(result.outline) == 3
        assert all(isinstance(item, OutlineItem) for item in result.outline)
        assert result.outline[0].heading == "Introduction"
        assert "introduction" in result.outline[0].description.lower()
    
    def test_brief_with_legacy_faq_format(self):
        """Test conversion of legacy FAQ format (q/a keys)."""
        brief_data = {
            "target_reader": "Users",
            "search_intent": "informational", 
            "angle": "Guide",
            "outline": [{"heading": "Test", "description": "Test desc"}],
            "key_entities": ["Test"],
            "faqs": [
                {"q": "What is this?", "a": "This is a test"},
                {"question": "Modern format?", "answer": "Yes, this works too"}
            ],
            "checklist": ["Item 1"],
            "meta_title": "Test",
            "meta_description": "Test description"
        }
        
        result = _validate_and_structure_brief(brief_data, "test")
        
        assert len(result.faqs) == 2
        assert result.faqs[0].question == "What is this?"
        assert result.faqs[0].answer == "This is a test"
        assert result.faqs[1].question == "Modern format?"
        assert result.faqs[1].answer == "Yes, this works too"
    
    def test_brief_with_missing_fields(self):
        """Test handling of brief data with missing fields."""
        brief_data = {
            "target_reader": "Users",
            # Missing other required fields
        }
        
        result = _validate_and_structure_brief(brief_data, "test keyword")
        
        assert isinstance(result, ContentBrief)
        assert "test keyword" in result.angle.lower()
        assert len(result.outline) > 0
        assert len(result.faqs) >= 0
        assert len(result.checklist) > 0
        assert result.meta_title
        assert result.meta_description
    
    def test_brief_with_corrupted_data(self):
        """Test fallback behavior for corrupted brief data."""
        # This should trigger the exception handler
        result = _validate_and_structure_brief(None, "test keyword")
        
        assert isinstance(result, ContentBrief)
        assert "test keyword" in result.target_reader
        assert len(result.outline) > 0
        assert result.outline[0].heading == "Introduction"
    
    def test_meta_field_length_limits(self):
        """Test that meta fields are properly truncated."""
        brief_data = {
            "target_reader": "Users",
            "search_intent": "informational",
            "angle": "Guide",
            "outline": [{"heading": "Test", "description": "Desc"}],
            "key_entities": ["Test"],
            "faqs": [],
            "checklist": ["Item"],
            "meta_title": "A" * 100,  # Too long
            "meta_description": "B" * 200  # Too long
        }
        
        result = _validate_and_structure_brief(brief_data, "test")
        
        assert len(result.meta_title) <= 60
        assert len(result.meta_description) <= 160


class TestBriefResponseStructure:
    """Test the complete brief response structure with heuristics."""
    
    def test_word_count_estimate_structure(self):
        """Test word count estimate meets schema requirements."""
        estimate = estimate_word_count("python tutorial", "informational", "medium")
        
        word_count_model = WordCountEstimate(
            min_words=estimate.min_words,
            max_words=estimate.max_words,
            target_words=estimate.target_words,
            reasoning=estimate.reasoning
        )
        
        assert isinstance(word_count_model.min_words, int)
        assert isinstance(word_count_model.max_words, int)
        assert isinstance(word_count_model.target_words, int)
        assert isinstance(word_count_model.reasoning, str)
        assert word_count_model.min_words < word_count_model.target_words < word_count_model.max_words
    
    def test_backlink_opportunities_structure(self):
        """Test backlink opportunities meet schema requirements."""
        buckets = recommend_backlink_buckets("python tutorial", "tech", "developers")
        
        backlink_models = [
            BacklinkOpportunity(
                category=bucket.category,
                websites=bucket.websites,
                reason=bucket.reason,
                difficulty=bucket.difficulty
            ) for bucket in buckets
        ]
        
        assert len(backlink_models) > 0
        for model in backlink_models:
            assert isinstance(model.category, str)
            assert isinstance(model.websites, list)
            assert isinstance(model.reason, str)
            assert model.difficulty in ["Easy", "Medium", "Hard"]
            assert len(model.websites) > 0
    
    def test_complete_content_brief_structure(self):
        """Test that complete ContentBrief model validation works."""
        # Create a complete brief with all fields
        outline = [
            OutlineItem(heading="Introduction", description="Intro to the topic"),
            OutlineItem(heading="Main Content", description="Core information")
        ]
        
        faqs = [
            FAQItem(question="What is this?", answer="This is a comprehensive guide")
        ]
        
        word_count = WordCountEstimate(
            min_words=1200,
            max_words=1800,
            target_words=1500,
            reasoning="Standard informational content length"
        )
        
        backlinks = [
            BacklinkOpportunity(
                category="Educational Resources",
                websites=["University sites", "Educational blogs"],
                reason="Authoritative educational content",
                difficulty="Medium"
            )
        ]
        
        brief = ContentBrief(
            target_reader="Software developers",
            search_intent="informational",
            angle="Comprehensive technical guide",
            outline=outline,
            key_entities=["Python", "Programming"],
            faqs=faqs,
            checklist=["Read documentation", "Practice coding"],
            meta_title="Python Programming Guide",
            meta_description="Complete guide to Python programming for developers",
            recommended_word_count=word_count,
            backlink_opportunities=backlinks
        )
        
        # Should not raise validation errors
        assert brief.target_reader == "Software developers"
        assert len(brief.outline) == 2
        assert len(brief.faqs) == 1
        assert brief.recommended_word_count.target_words == 1500
        assert len(brief.backlink_opportunities) == 1


class TestHeuristicsIntegration:
    """Test integration of heuristics with brief generation."""
    
    def test_search_intent_affects_word_count(self):
        """Test that search intent from brief affects word count calculation."""
        keyword = "python tutorial"
        
        informational_count = estimate_word_count(keyword, "informational", "medium")
        transactional_count = estimate_word_count(keyword, "transactional", "medium")
        
        assert informational_count.target_words > transactional_count.target_words
    
    def test_target_reader_affects_backlinks(self):
        """Test that target reader affects backlink recommendations."""
        keyword = "project management"
        
        b2b_links = recommend_backlink_buckets(keyword, "business", "business managers")
        consumer_links = recommend_backlink_buckets(keyword, "general", "personal users")
        
        b2b_categories = [link.category.lower() for link in b2b_links]
        consumer_categories = [link.category.lower() for link in consumer_links]
        
        # Should have some different categories
        assert b2b_categories != consumer_categories
    
    def test_keyword_type_affects_recommendations(self):
        """Test that keyword type affects both word count and backlinks."""
        how_to_keyword = "how to learn programming"
        comparison_keyword = "python vs java"
        
        # Word count should differ
        how_to_count = estimate_word_count(how_to_keyword, "informational", "medium")
        comparison_count = estimate_word_count(comparison_keyword, "commercial", "medium")
        
        assert how_to_count.target_words != comparison_count.target_words
        
        # Backlink categories should differ
        how_to_links = recommend_backlink_buckets(how_to_keyword, "tech", "beginners")
        comparison_links = recommend_backlink_buckets(comparison_keyword, "tech", "developers")
        
        how_to_categories = [link.category.lower() for link in how_to_links]
        comparison_categories = [link.category.lower() for link in comparison_links]
        
        # Tutorial content should get educational resources
        assert any("tutorial" in cat or "educational" in cat for cat in how_to_categories)


class TestErrorHandling:
    """Test error handling in brief generation."""
    
    def test_invalid_search_intent_defaults(self):
        """Test handling of invalid search intent values."""
        # Should default to reasonable values without crashing
        result = estimate_word_count("test", "invalid_intent", "medium")
        
        assert isinstance(result.target_words, int)
        assert result.target_words > 0
    
    def test_invalid_competition_level_defaults(self):
        """Test handling of invalid competition level values."""
        result = estimate_word_count("test", "informational", "invalid_level")
        
        assert isinstance(result.target_words, int)
        assert result.target_words > 0
    
    def test_empty_keyword_handling(self):
        """Test handling of empty or None keywords."""
        result = estimate_word_count("", "informational", "medium")
        
        assert isinstance(result.target_words, int)
        assert result.target_words >= 300
        
        backlinks = recommend_backlink_buckets("", "general", "")
        assert len(backlinks) > 0  # Should still provide some recommendations
    
    def test_extreme_keyword_lengths(self):
        """Test handling of very long keywords."""
        long_keyword = " ".join(["word"] * 50)
        
        result = estimate_word_count(long_keyword, "informational", "medium")
        assert isinstance(result.target_words, int)
        
        backlinks = recommend_backlink_buckets(long_keyword, "general", "users")
        assert len(backlinks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])