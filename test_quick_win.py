#!/usr/bin/env python3
"""
Quick test for Quick Win keyword extraction functionality
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re

def extract_quick_win_keywords(gpt_response: str):
    """
    Extract Quick Win keywords from GPT analysis response.
    """
    # Look for Quick Win sections with numbered lists
    quick_win_patterns = [
        r"### 🔥 Quick Win Keywords?:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"Quick Win Keywords?:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"🔥.*Quick Win.*:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"### Quick Wins?:?\s*\n((?:\d+\.\s.+\n?)+)",
        r"## Quick Win.*:?\s*\n((?:\d+\.\s.+\n?)+)"
    ]
    
    quick_wins = []
    
    for pattern in quick_win_patterns:
        matches = re.search(pattern, gpt_response, re.MULTILINE | re.IGNORECASE)
        if matches:
            lines = matches.group(1).strip().split('\n')
            for line in lines:
                # Extract keyword from numbered list
                keyword_match = re.match(r'\d+\.\s*(.+)', line.strip())
                if keyword_match:
                    keyword = keyword_match.group(1).strip()
                    # Clean up any extra formatting
                    keyword = re.sub(r'\*\*|\*|`', '', keyword)
                    if keyword and len(keyword) > 3:  # Basic validation
                        quick_wins.append(keyword)
    
    # Remove duplicates and limit results
    return list(dict.fromkeys(quick_wins))[:5]

# Test GPT response with Quick Win keywords
test_gpt_response = """
## Keyword Analysis Results

### 🔥 Quick Win Keywords:
1. podcast mic under $100
2. best budget microphone
3. USB mic for Zoom calls
4. affordable recording equipment
5. cheap podcast setup

### Other Analysis
Some other content here...

### Recommendations
- Focus on long-tail keywords
- Target buyer intent terms
"""

def test_extraction():
    """Test the Quick Win keyword extraction"""
    print("Testing Quick Win extraction...")
    
    keywords = extract_quick_win_keywords(test_gpt_response)
    
    print(f"Extracted {len(keywords)} keywords:")
    for i, kw in enumerate(keywords, 1):
        print(f"{i}. {kw}")
    
    # Expected keywords
    expected = [
        "podcast mic under $100",
        "best budget microphone", 
        "USB mic for Zoom calls",
        "affordable recording equipment",
        "cheap podcast setup"
    ]
    
    print(f"\nExpected: {len(expected)}")
    print(f"Found: {len(keywords)}")
    print(f"Match: {keywords == expected}")

if __name__ == "__main__":
    test_extraction()
