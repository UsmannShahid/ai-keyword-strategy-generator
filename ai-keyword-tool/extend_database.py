#!/usr/bin/env python3
"""
Extend the database with new tables for suggestions and SERP data.
Run this once to add the new tables to your existing database.
"""

from core.db import init_db, extend_db

def main():
    print("🗃️ Extending database with new tables...")
    
    # Initialize base tables (safe if they already exist)
    init_db()
    
    # Extend with new tables
    extend_db()
    
    print("✅ Database extension complete!")
    print("New tables added:")
    print("  - suggestions (for AI-generated content suggestions)")
    print("  - serps (for SERP analysis data)")

if __name__ == "__main__":
    main()
