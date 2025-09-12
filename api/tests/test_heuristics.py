# api/tests/test_heuristics.py
import pytest
from api.core.heuristics import (
    estimate_word_count, 
    recommend_backlink_buckets, 
    analyze_keyword_characteristics
)

class TestWordCountEstimation:
    """Test word count estimation heuristics."""
    
    def test_informational_intent_increases_word_count(self):
        """Informational content should require more words."""
        result = estimate_word_count("python tutorial", "informational", "medium")
        
        assert result.min_words >= 300
        assert result.max_words <= 5000
        assert result.target_words > result.min_words
        assert result.target_words < result.max_words
        assert "informational" in result.reasoning.lower()
    
    def test_transactional_intent_reduces_word_count(self):
        """Transactional content should be shorter."""
        transactional = estimate_word_count("buy python course", "transactional", "medium")
        informational = estimate_word_count("python tutorial", "informational", "medium")
        
        assert transactional.target_words < informational.target_words
    
    def test_high_competition_increases_word_count(self):
        """High competition should require more comprehensive content."""
        high_comp = estimate_word_count("python", "informational", "high")
        low_comp = estimate_word_count("python", "informational", "low")
        
        assert high_comp.target_words > low_comp.target_words
    
    def test_how_to_keywords_increase_word_count(self):
        """How-to keywords should require detailed explanations."""
        how_to = estimate_word_count("how to learn python", "informational", "medium")
        simple = estimate_word_count("python", "informational", "medium")
        
        assert how_to.target_words > simple.target_words
        assert "tutorial" in how_to.reasoning.lower() or "step-by-step" in how_to.reasoning.lower()
    
    def test_comparison_keywords_moderate_length(self):
        """Comparison keywords should have moderate length."""
        comparison = estimate_word_count("python vs java", "commercial", "medium")
        
        assert 1000 <= comparison.target_words <= 2500
    
    def test_word_count_bounds(self):
        """Word count should always be within reasonable bounds."""
        result = estimate_word_count("test keyword", "informational", "high")
        
        assert result.min_words >= 300
        assert result.max_words <= 5000
        assert result.min_words < result.target_words < result.max_words
    
    def test_reasoning_provided(self):
        """All estimates should include reasoning."""
        result = estimate_word_count("advanced python tutorial", "informational", "high")
        
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 10


class TestBacklinkRecommendations:
    """Test backlink opportunity recommendations."""
    
    def test_tech_industry_recommendations(self):
        """Tech industry should get relevant directories."""
        buckets = recommend_backlink_buckets("python framework", "tech", "developers")
        
        tech_bucket = next((b for b in buckets if "tech" in b.category.lower()), None)
        assert tech_bucket is not None
        assert any("ProductHunt" in site or "GitHub" in site for site in tech_bucket.websites)
    
    def test_health_industry_recommendations(self):
        """Health industry should get medical authorities."""
        buckets = recommend_backlink_buckets("nutrition guide", "health", "health-conscious consumers")
        
        health_bucket = next((b for b in buckets if "health" in b.category.lower()), None)
        assert health_bucket is not None
        assert any("Healthline" in site or "WebMD" in site for site in health_bucket.websites)
    
    def test_how_to_content_gets_tutorial_sites(self):
        """How-to content should recommend tutorial platforms."""
        buckets = recommend_backlink_buckets("how to cook pasta", "general", "home cooks")
        
        tutorial_bucket = next((b for b in buckets if "tutorial" in b.category.lower()), None)
        assert tutorial_bucket is not None
        assert any("WikiHow" in site or "YouTube" in site for site in tutorial_bucket.websites)
    
    def test_tool_keywords_get_directories(self):
        """Tool keywords should recommend tool directories."""
        buckets = recommend_backlink_buckets("project management tool", "tech", "business users")
        
        tool_bucket = next((b for b in buckets if "tool" in b.category.lower() or "directories" in b.category.lower()), None)
        assert tool_bucket is not None
    
    def test_local_keywords_get_local_opportunities(self):
        """Local keywords should recommend local resources."""
        buckets = recommend_backlink_buckets("restaurants near me", "general", "local consumers")
        
        local_bucket = next((b for b in buckets if "local" in b.category.lower()), None)
        assert local_bucket is not None
        assert any("Chamber of Commerce" in site or "Local" in site for site in local_bucket.websites)
    
    def test_bucket_structure_validation(self):
        """All buckets should have required fields."""
        buckets = recommend_backlink_buckets("test keyword", "general", "general audience")
        
        assert len(buckets) > 0
        for bucket in buckets:
            assert hasattr(bucket, 'category')
            assert hasattr(bucket, 'websites')
            assert hasattr(bucket, 'reason')
            assert hasattr(bucket, 'difficulty')
            assert bucket.difficulty in ["Easy", "Medium", "Hard"]
            assert len(bucket.websites) > 0
            assert len(bucket.category) > 0
            assert len(bucket.reason) > 0
    
    def test_maximum_buckets_limit(self):
        """Should not return more than 6 buckets."""
        buckets = recommend_backlink_buckets("complex keyword", "tech", "developers")
        
        assert len(buckets) <= 6
    
    def test_b2b_vs_b2c_targeting(self):
        """B2B and B2C should get different recommendations."""
        b2b_buckets = recommend_backlink_buckets("enterprise software", "tech", "business decision makers")
        b2c_buckets = recommend_backlink_buckets("mobile app", "tech", "consumers")
        
        # B2B should have business publications
        b2b_categories = [b.category.lower() for b in b2b_buckets]
        b2c_categories = [b.category.lower() for b in b2c_buckets]
        
        # Categories should be different between B2B and B2C
        assert b2b_categories != b2c_categories


class TestKeywordAnalysis:
    """Test keyword characteristic analysis."""
    
    def test_intent_detection(self):
        """Should correctly detect search intent signals."""
        informational = analyze_keyword_characteristics("how to learn python")
        commercial = analyze_keyword_characteristics("best python course")
        transactional = analyze_keyword_characteristics("buy python book")
        navigational = analyze_keyword_characteristics("python.org login")
        
        assert informational["estimated_intent"] == "informational"
        assert commercial["estimated_intent"] == "commercial"
        assert transactional["estimated_intent"] == "transactional"
        assert navigational["estimated_intent"] == "navigational"
    
    def test_complexity_detection(self):
        """Should detect complexity indicators."""
        simple = analyze_keyword_characteristics("basic python tutorial")
        complex = analyze_keyword_characteristics("advanced enterprise python architecture")
        
        assert simple["complexity"] == "low"
        assert complex["complexity"] == "high"
    
    def test_long_tail_detection(self):
        """Should identify long-tail keywords."""
        short = analyze_keyword_characteristics("python")
        long_tail = analyze_keyword_characteristics("how to learn python for beginners")
        
        assert not short["is_long_tail"]
        assert long_tail["is_long_tail"]
    
    def test_question_detection(self):
        """Should identify question keywords."""
        question = analyze_keyword_characteristics("what is python programming")
        statement = analyze_keyword_characteristics("python programming tutorial")
        
        assert question["is_question"]
        assert not statement["is_question"]
    
    def test_comparison_detection(self):
        """Should identify comparison keywords."""
        comparison = analyze_keyword_characteristics("python vs java")
        single = analyze_keyword_characteristics("python tutorial")
        
        assert comparison["is_comparison"]
        assert not single["is_comparison"]
    
    def test_branded_detection(self):
        """Should identify branded keywords."""
        branded = analyze_keyword_characteristics("google python course")
        generic = analyze_keyword_characteristics("python course")
        
        assert branded["is_branded"]
        assert not generic["is_branded"]
    
    def test_local_detection(self):
        """Should identify local keywords."""
        local = analyze_keyword_characteristics("python classes near me")
        global_kw = analyze_keyword_characteristics("python tutorial")
        
        assert local["is_local"]
        assert not global_kw["is_local"]
    
    def test_word_count_accuracy(self):
        """Should correctly count words."""
        single = analyze_keyword_characteristics("python")
        multiple = analyze_keyword_characteristics("learn python programming online")
        
        assert single["word_count"] == 1
        assert multiple["word_count"] == 4


class TestIntegration:
    """Integration tests for combined heuristics."""
    
    def test_how_to_keyword_full_pipeline(self):
        """Test complete pipeline for how-to keyword."""
        keyword = "how to learn machine learning"
        
        # Analyze characteristics
        analysis = analyze_keyword_characteristics(keyword)
        assert analysis["estimated_intent"] == "informational"
        assert analysis["is_question"]
        assert analysis["is_long_tail"]
        
        # Estimate word count
        word_count = estimate_word_count(keyword, analysis["estimated_intent"], "medium")
        assert word_count.target_words > 1500  # Should be comprehensive
        
        # Get backlink opportunities
        backlinks = recommend_backlink_buckets(keyword, "tech", "students and professionals")
        assert len(backlinks) > 0
        
        # Should include educational resources
        categories = [b.category.lower() for b in backlinks]
        assert any("educational" in cat or "tutorial" in cat for cat in categories)
    
    def test_commercial_keyword_pipeline(self):
        """Test pipeline for commercial intent keyword."""
        keyword = "best project management software"
        
        analysis = analyze_keyword_characteristics(keyword)
        assert analysis["estimated_intent"] == "commercial"
        assert analysis["is_comparison"]
        
        word_count = estimate_word_count(keyword, analysis["estimated_intent"], "high")
        assert 1200 <= word_count.target_words <= 2500  # Moderate length for comparison
        
        backlinks = recommend_backlink_buckets(keyword, "tech", "business users")
        categories = [b.category.lower() for b in backlinks]
        assert any("review" in cat or "tool" in cat or "b2b" in cat for cat in categories)
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty keyword
        word_count = estimate_word_count("", "informational", "medium")
        assert word_count.min_words >= 300
        
        # Very long keyword
        long_keyword = " ".join(["word"] * 20)
        analysis = analyze_keyword_characteristics(long_keyword)
        assert analysis["word_count"] == 20
        assert analysis["is_long_tail"]
        
        # Special characters
        special_keyword = "how-to: learn python (2024 guide)!"
        analysis = analyze_keyword_characteristics(special_keyword)
        assert analysis["estimated_intent"] == "informational"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])