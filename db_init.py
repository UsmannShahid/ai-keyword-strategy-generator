"""
Database initialization check for the app.
This ensures the database is ready before the app starts.
"""

def ensure_db_initialized():
    """Ensure the database is initialized before the app runs."""
    try:
        import sys
        import os
        # Add the ai-keyword-tool subdirectory to path
        ai_tool_dir = os.path.join(os.path.dirname(__file__), 'ai-keyword-tool')
        if ai_tool_dir not in sys.path:
            sys.path.append(ai_tool_dir)
        
        from core.db import init_db, extend_db
        
        # Initialize base tables and extend with new tables
        init_db()
        extend_db()
        print("✅ Database fully initialized with all tables")
        return True
    except ImportError as e:
        print(f"❌ Import error: Could not import database module: {e}")
        print("Make sure the core/db.py file exists in the ai-keyword-tool directory")
        return False
    except Exception as e:
        print(f"⚠️ Warning: Database initialization failed: {e}")
        return False

# Initialize database when module is imported
ensure_db_initialized()
