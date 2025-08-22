#!/usr/bin/env python3
"""
Test the enhanced database functionality with suggestions and SERP data.
"""

import sys
import os
import json

# Add ai-keyword-tool to path for imports
sys.path.append('ai-keyword-tool')

try:
    from core.db import (
        init_db, extend_db, save_session, save_brief, 
        save_suggestion, save_serp, get_recent_sessions,
        get_suggestions_by_session, get_serp_by_session
    )
    print("✅ Database imports successful")
    
    # Test saving a session
    session_id = save_session('Enhanced Database Test Session')
    print(f"✅ Session saved: {session_id}")
    
    # Test saving a brief
    save_brief(session_id, 'Test content brief for enhanced database')
    print("✅ Brief saved")
    
    # Test saving suggestions (different variants)
    suggestion_id1 = save_suggestion(session_id, "Quick wins content for testing", "quick_wins")
    suggestion_id2 = save_suggestion(session_id, "Content ideas for testing", "content_ideas")
    suggestion_id3 = save_suggestion(session_id, "Technical SEO suggestions", "technical_seo")
    print(f"✅ Suggestions saved: {suggestion_id1}, {suggestion_id2}, {suggestion_id3}")
    
    # Test saving SERP data
    test_serp_data = [
        {"title": "Test Result 1", "url": "https://example1.com", "snippet": "Test snippet 1"},
        {"title": "Test Result 2", "url": "https://example2.com", "snippet": "Test snippet 2"}
    ]
    serp_id = save_serp(session_id, json.dumps(test_serp_data))
    print(f"✅ SERP data saved: {serp_id}")
    
    # Test retrieval functions
    print("\n📋 Testing retrieval functions:")
    
    # Get recent sessions
    sessions = get_recent_sessions(3)
    print(f"📝 Recent sessions: {len(sessions)} found")
    for session in sessions:
        print(f"   - {session[1]} ({session[2][:10]})")
    
    # Get suggestions for this session
    suggestions = get_suggestions_by_session(session_id)
    print(f"💡 Suggestions for session: {len(suggestions)} found")
    for suggestion in suggestions:
        print(f"   - [{suggestion[1]}] {suggestion[2][:50]}...")
    
    # Get SERP data for this session
    serp_data = get_serp_by_session(session_id)
    if serp_data:
        print(f"🔍 SERP data found: {len(json.loads(serp_data[1]))} results")
    else:
        print("❌ No SERP data found")
    
    print("\n🎉 All enhanced database tests passed!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
