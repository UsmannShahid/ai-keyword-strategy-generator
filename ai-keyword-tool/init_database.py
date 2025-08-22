#!/usr/bin/env python3
"""
Database initialization script.
Run this once to set up the SQLite database with required tables.
"""

from core.db import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete!")
