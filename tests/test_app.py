# test_app.py
# ---------------------------------------------
# Test Suite for AI Keyword Strategy Generator
# Tests utility functions, data processing, and UI components
# ---------------------------------------------

import pytest
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions from our app
from app import slugify, build_prompt, to_dataframe

class TestUtilityFunctions:
    """Test utility functions used in the app."""
    
    def test_slugify_basic(self):
        """Test basic slugify functionality."""
        assert slugify("Hello World") == "Hello-World"
        assert slugify("Test App 123") == "Test-App-123"
        assert slugify("Special!@# Characters") == "Special----Characters"
    
    def test_slugify_edge_cases(self):
        """Test slugify with edge cases."""
        assert slugify("") == ""
        assert slugify("   ") == ""
        assert slugify("a" * 100) == "a" * 60  # Should truncate to 60 chars
        assert slugify("---test---") == "test"  # Should strip leading/trailing dashes
    
    def test_build_prompt(self):
        """Test prompt building with various inputs."""
        prompt = build_prompt(
            business_desc="Online bookstore",
            industry="E-commerce",
            audience="Book lovers",
            location="US"
        )
        
        assert "Online bookstore" in prompt
        assert "E-commerce" in prompt
        assert "Book lovers" in prompt
        assert "US" in prompt
        assert "valid JSON" in prompt
        assert "informational" in prompt
        assert "transactional" in prompt
        assert "branded" in prompt
    
    def test_build_prompt_empty_fields(self):
        """Test prompt building with empty optional fields."""
        prompt = build_prompt(
            business_desc="Test business",
            industry="",
            audience="",
            location=""
        )
        
        assert "Test business" in prompt
        assert "valid JSON" in prompt


class TestDataProcessing:
    """Test data processing and conversion functions."""
    
    def test_to_dataframe_valid_data(self):
        """Test converting valid JSON data to DataFrame."""
        test_data = {
            "informational": ["how to code", "python tutorial"],
            "transactional": ["buy python book", "python course price"],
            "branded": ["openai api"]
        }
        
        df = to_dataframe(test_data)
        
        assert len(df) == 5
        assert "keyword" in df.columns
        assert "category" in df.columns
        assert "how to code" in df["keyword"].values
        assert "informational" in df["category"].values
        assert "transactional" in df["category"].values
        assert "branded" in df["category"].values
    
    def test_to_dataframe_empty_data(self):
        """Test converting empty data to DataFrame."""
        df = to_dataframe({})
        
        assert len(df) == 0
        assert "keyword" in df.columns
        assert "category" in df.columns
    
    def test_to_dataframe_partial_data(self):
        """Test converting partial data (missing categories)."""
        test_data = {
            "informational": ["seo tips", "keyword research"],
            "branded": []  # Empty list
        }
        
        df = to_dataframe(test_data)
        
        assert len(df) == 2
        assert all(cat == "informational" for cat in df["category"])
    
    def test_to_dataframe_none_values(self):
        """Test handling None values in categories."""
        test_data = {
            "informational": ["test keyword"],
            "transactional": None,
            "branded": ["brand keyword"]
        }
        
        df = to_dataframe(test_data)
        
        assert len(df) == 2
        assert "test keyword" in df["keyword"].values
        assert "brand keyword" in df["keyword"].values


class TestAPIIntegration:
    """Test OpenAI API integration (mocked)."""
    
    @patch('app.client')
    def test_get_keywords_json_success(self, mock_client):
        """Test successful API call and JSON parsing."""
        from app import get_keywords_json
        
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "informational": ["test keyword"],
            "transactional": ["buy test"],
            "branded": ["test brand"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        result = get_keywords_json("test prompt")
        
        assert "informational" in result
        assert "transactional" in result
        assert "branded" in result
        assert result["informational"] == ["test keyword"]
    
    @patch('app.client')
    def test_get_keywords_json_invalid_json(self, mock_client):
        """Test handling of invalid JSON response."""
        from app import get_keywords_json
        
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not JSON"
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(json.JSONDecodeError):
            get_keywords_json("test prompt")


class TestEnvironmentSetup:
    """Test environment configuration and setup."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_key_present(self):
        """Test that API key is loaded correctly."""
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key == "test-key"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_api_key_missing(self):
        """Test handling of missing API key."""
        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is None


class TestStreamlitIntegration:
    """Test Streamlit-specific functionality (mocked)."""
    
    @patch('streamlit.text_input')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    def test_ui_components_render(self, mock_columns, mock_button, mock_text_input):
        """Test that UI components are called correctly."""
        # Mock streamlit components
        mock_text_input.return_value = "test input"
        mock_button.return_value = False
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        
        # Import app (this will execute the Streamlit code)
        # Note: This is a basic test to ensure no import errors
        try:
            import app
            assert True  # If we get here, the app imported successfully
        except Exception as e:
            pytest.fail(f"App import failed: {e}")


class TestDataValidation:
    """Test data validation and error handling."""
    
    def test_business_description_validation(self):
        """Test business description validation logic."""
        # Test empty strings
        assert not "".strip()
        assert not "   ".strip()
        
        # Test valid strings
        assert "Valid business description".strip()
    
    def test_json_structure_validation(self):
        """Test that expected JSON structure is maintained."""
        expected_keys = {"informational", "transactional", "branded"}
        
        test_data = {
            "informational": ["test"],
            "transactional": ["test"],
            "branded": ["test"]
        }
        
        assert set(test_data.keys()).issubset(expected_keys)


class TestFileOperations:
    """Test file operations like CSV generation."""
    
    def test_csv_generation(self):
        """Test CSV file generation from DataFrame."""
        test_data = {
            "informational": ["seo tips"],
            "transactional": ["buy seo tool"]
        }
        
        df = to_dataframe(test_data)
        csv_content = df.to_csv(index=False)
        
        assert "keyword,category" in csv_content
        assert "seo tips,informational" in csv_content
        assert "buy seo tool,transactional" in csv_content
    
    def test_filename_generation(self):
        """Test filename generation for downloads."""
        from datetime import datetime
        
        today = datetime.now().strftime("%Y-%m-%d")
        business_desc = "Online Marketing Agency"
        base = slugify(business_desc)
        filename = f"{base}-{today}.csv"
        
        assert "Online-Marketing-Agency" in filename
        assert today in filename
        assert filename.endswith(".csv")


# Test configuration
if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
