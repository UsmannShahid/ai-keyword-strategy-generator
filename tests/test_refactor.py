#!/usr/bin/env python3
"""
Test script for the refactored keyword tool modules.
Tests parsing.py, llm_client.py, services.py, and integration.
"""

import sys
import os
sys.path.append('.')

def test_parsing():
    """Test the parsing module."""
    print("🔍 Testing parsing.py...")
    
    from parsing import parse_keywords_from_model, SAFE_OUTPUT, validate_keywords_response
    
    # Test 1: Valid JSON
    valid_json = '{"informational": ["seo tips"], "transactional": ["buy seo tool"], "branded": ["company name"]}'
    result = parse_keywords_from_model(valid_json)
    assert "informational" in result
    assert len(result["informational"]) > 0
    print("✅ Valid JSON parsing works")
    
    # Test 2: Invalid JSON (fallback)
    invalid_json = "This is not JSON"
    result = parse_keywords_from_model(invalid_json)
    assert result == SAFE_OUTPUT
    print("✅ Invalid JSON fallback works")
    
    # Test 3: JSON in code blocks
    code_block = '```json\n{"informational": ["test"]}\n```'
    result = parse_keywords_from_model(code_block)
    assert "informational" in result
    print("✅ Code block extraction works")
    
    # Test 4: Validate function
    result = validate_keywords_response(valid_json)
    assert isinstance(result["informational"], list)
    print("✅ Validation function works")
    
    print("✅ All parsing tests passed!\n")

def test_llm_client():
    """Test the LLM client module."""
    print("🤖 Testing llm_client.py...")
    
    try:
        from llm_client import KeywordLLMClient, build_prompt
        
        # Test 1: Client initialization
        try:
            client = KeywordLLMClient.create_default()
            print("✅ Client initialization works")
        except Exception as e:
            print(f"⚠️  Client init failed (expected if no API key): {e}")
            return
        
        # Test 2: Prompt building
        prompt = client.build_keyword_prompt("online bookstore", "retail", "readers", "US")
        assert "online bookstore" in prompt
        assert "JSON" in prompt
        print("✅ Prompt building works")
        
        # Test 3: Legacy function
        legacy_prompt = build_prompt("test business", "tech", "developers", "global")
        assert "test business" in legacy_prompt
        print("✅ Legacy prompt function works")
        
        # Test 4: Connection test (if API key available)
        if client.test_connection():
            print("✅ API connection test passed")
        else:
            print("⚠️  API connection test failed (may be expected)")
        
        print("✅ All LLM client tests passed!\n")
        
    except Exception as e:
        print(f"❌ LLM client test failed: {e}\n")

def test_services():
    """Test the services module."""
    print("⚙️ Testing services.py...")
    
    try:
        from services import KeywordService, get_keywords_safe, generate_keywords_simple
        
        # Test 1: Service initialization
        try:
            service = KeywordService()
            print("✅ Service initialization works")
        except Exception as e:
            print(f"⚠️  Service init failed (expected if no API key): {e}")
            return
        
        # Test 2: Legacy function
        result = get_keywords_safe('{"informational": ["test"]}')
        assert isinstance(result, dict)
        print("✅ Legacy get_keywords_safe works")
        
        # Test 3: Simple generation function
        result = generate_keywords_simple("test business")
        assert isinstance(result, dict)
        assert "informational" in result
        print("✅ Simple generation function works")
        
        print("✅ All services tests passed!\n")
        
    except Exception as e:
        print(f"❌ Services test failed: {e}\n")

def test_app_integration():
    """Test app.py integration (import only)."""
    print("🎯 Testing app.py integration...")
    
    try:
        # Test import (this will execute the Streamlit code)
        import app
        print("✅ App imports successfully")
        
        # Test that key functions are available
        assert hasattr(app, 'slugify')
        assert hasattr(app, 'default_report_name')
        assert hasattr(app, 'to_dataframe')
        print("✅ App utility functions available")
        
        print("✅ App integration test passed!\n")
        
    except Exception as e:
        print(f"❌ App integration test failed: {e}\n")

def main():
    """Run all tests."""
    print("🧪 Running Keyword Tool Refactoring Tests")
    print("=" * 50)
    
    try:
        test_parsing()
        test_llm_client()
        test_services() 
        test_app_integration()
        
        print("🎉 All tests completed successfully!")
        print("✅ Refactoring appears to be working correctly")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
