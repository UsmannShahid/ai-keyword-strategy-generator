"""
Database initialization script
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from core.database import Base, DATABASE_URL
from models.database import (
    KeywordQuery, KeywordCache, ContentBrief, 
    BriefCache, UserSession
)

async def init_database():
    """Initialize database tables"""
    print(f"Connecting to database: {DATABASE_URL}")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise
    finally:
        await engine.dispose()

async def drop_database():
    """Drop all database tables (use with caution!)"""
    print(f"Dropping all tables from: {DATABASE_URL}")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ Database tables dropped successfully!")
            
    except Exception as e:
        print(f"❌ Error dropping database tables: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        asyncio.run(drop_database())
    else:
        asyncio.run(init_database())