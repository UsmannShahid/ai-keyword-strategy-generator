# test_utils.py
import pytest
from datetime import date
from utils import slugify, default_report_name


class TestSlugify:
    """Test the slugify function."""
    
    def test_basic_slugification(self):
        """Test basic string to slug conversion."""
        assert slugify("Digital Marketing") == "digital-marketing"
        assert slugify("SEO Optimization") == "seo-optimization"
        assert slugify("Content Strategy") == "content-strategy"
    
    def test_special_characters(self):
        """Test handling of special characters."""
        assert slugify("E-commerce & Retail") == "e-commerce-retail"
        assert slugify("AI/ML Solutions") == "ai-ml-solutions"
        assert slugify("Healthcare @ 2025") == "healthcare-2025"
        assert slugify("Tech (Software)") == "tech-software"
    
    def test_multiple_spaces_and_hyphens(self):
        """Test handling of multiple spaces and consecutive hyphens."""
        assert slugify("  Multiple   Spaces  ") == "multiple-spaces"
        assert slugify("Already--Has---Hyphens") == "already-has-hyphens"
        assert slugify("Mixed  --  Spacing") == "mixed-spacing"
    
    def test_edge_cases(self):
        """Test edge cases and empty inputs."""
        assert slugify("") == "report"
        assert slugify(None) == "report"
        assert slugify("   ") == "report"
        assert slugify("123") == "123"
        assert slugify("!@#$%^&*()") == "report"
    
    def test_unicode_and_accents(self):
        """Test handling of unicode and accented characters."""
        assert slugify("Café & Restaurant") == "caf-restaurant"
        assert slugify("Naïve Approach") == "na-ve-approach"
        assert slugify("São Paulo Business") == "s-o-paulo-business"
    
    def test_numbers_and_alphanumeric(self):
        """Test handling of numbers and alphanumeric strings."""
        assert slugify("Web 3.0 Development") == "web-3-0-development"
        assert slugify("COVID-19 Impact") == "covid-19-impact"
        assert slugify("B2B SaaS Solutions") == "b2b-saas-solutions"


class TestDefaultReportName:
    """Test the default_report_name function."""
    
    def test_with_business_description(self):
        """Test report name generation with business description."""
        today = date.today().strftime("%Y-%m-%d")
        
        result = default_report_name("Digital Marketing Agency")
        expected = f"digital-marketing-agency-{today}"
        assert result == expected
        
        result = default_report_name("E-commerce Store")
        expected = f"e-commerce-store-{today}"
        assert result == expected
    
    def test_with_empty_business_description(self):
        """Test report name generation with empty business description."""
        today = date.today().strftime("%Y-%m-%d")
        
        assert default_report_name("") == f"report-{today}"
        assert default_report_name(None) == f"report-{today}"
        assert default_report_name("   ") == f"report-{today}"
    
    def test_with_special_characters_in_business(self):
        """Test report name generation with special characters in business."""
        today = date.today().strftime("%Y-%m-%d")
        
        result = default_report_name("Tech & Innovation Co.")
        expected = f"tech-innovation-co-{today}"
        assert result == expected
        
        result = default_report_name("AI/ML Consulting (2025)")
        expected = f"ai-ml-consulting-2025-{today}"
        assert result == expected
    
    def test_date_format(self):
        """Test that the date format is correct."""
        result = default_report_name("test")
        today = date.today().strftime("%Y-%m-%d")
        assert result.endswith(today)
        assert len(result.split("-")) >= 4  # At least "test" + 3 date parts
    
    def test_fallback_behavior(self):
        """Test fallback behavior for edge cases."""
        today = date.today().strftime("%Y-%m-%d")
        
        # Special characters only
        result = default_report_name("!@#$%^&*()")
        assert result == f"report-{today}"
        
        # Unicode characters
        result = default_report_name("Café & Résumé")
        expected = f"caf-r-sum-{today}"
        assert result == expected


class TestUtilsIntegration:
    """Integration tests for utils functions working together."""
    
    def test_slugify_and_report_name_consistency(self):
        """Test that slugify and default_report_name work consistently."""
        business = "Digital Marketing & SEO"
        report_name = default_report_name(business)
        
        # Extract the business part (everything except the date)
        parts = report_name.split("-")
        business_part = "-".join(parts[:-3])  # Remove YYYY-MM-DD
        
        # Should match direct slugification
        assert business_part == slugify(business)
    
    def test_real_world_scenarios(self):
        """Test with real-world business scenarios."""
        today = date.today().strftime("%Y-%m-%d")
        
        scenarios = [
            ("Healthcare Clinic", f"healthcare-clinic-{today}"),
            ("Restaurant & Catering", f"restaurant-catering-{today}"),
            ("B2B Software Solutions", f"b2b-software-solutions-{today}"),
            ("Fitness & Wellness Center", f"fitness-wellness-center-{today}"),
            ("E-learning Platform", f"e-learning-platform-{today}")
        ]
        
        for business, expected in scenarios:
            assert default_report_name(business) == expected
    
    def test_filename_safety(self):
        """Test that generated names are safe for file systems."""
        dangerous_inputs = [
            "../../etc/passwd",
            "con.txt",  # Windows reserved
            "file.exe",
            "file with spaces",
            "file/with\\slashes"
        ]
        
        for dangerous_input in dangerous_inputs:
            result = default_report_name(dangerous_input)
            # Should not contain dangerous characters
            assert "/" not in result
            assert "\\" not in result
            assert ".." not in result
            # Should be safe filename
            assert result.replace("-", "").replace(".", "").isalnum() or result.startswith("report-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
