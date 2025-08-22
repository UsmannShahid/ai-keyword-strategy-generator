#!/usr/bin/env python3
"""
Test script for database functionality.
This script demonstrates how to use the core.db functions.
"""

from core.db import init_db, save_session, save_brief, get_recent_sessions

# Initialize the database
init_db()

# Create a new session and save a brief
session_id = save_session("how to use sqlite with ai")
save_brief(session_id, "This is a sample AI-generated brief.")

# Display recent sessions
print("Recent sessions:")
for s in get_recent_sessions():
    print(s)
