"""
Startup script for initializing database on first run
"""

import asyncio
import os
from core.init_db import init_database

async def startup_tasks():
    """Run startup tasks"""
    print("🚀 Starting Quick Wins Finder API...")
    
    # Initialize database if it doesn't exist
    try:
        await init_database()
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        # Don't fail startup if database init fails
        # This allows the app to start even if DB is temporarily unavailable
    
    print("✅ Startup tasks completed!")

if __name__ == "__main__":
    asyncio.run(startup_tasks())