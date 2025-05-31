#!/usr/bin/env python3
"""
Simple migration runner script
Usage: python run_migration.py
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrations.create_collections import MongoMigration

def run_migration():
    """Run the database migration"""
    print("🚀 Running IoT Database Migration...")
    migration = MongoMigration()
    success = migration.create_collections_and_indexes()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("Your database is ready for IoT data collection.")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()