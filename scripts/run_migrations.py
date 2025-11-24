#!/usr/bin/env python3
"""
TradLab Migration Runner

Runs SQL migrations from DB/migrations/ folder.
Usage: python scripts/run_migrations.py
"""
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import psycopg2
from dotenv import load_dotenv


def run_migrations():
    """Run all SQL migrations from DB/migrations folder."""
    # Load environment variables
    load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment")
        print("   Please set DATABASE_URL in .env file")
        sys.exit(1)

    # Find migrations directory
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / "DB" / "migrations"

    if not migrations_dir.exists():
        print(f"❌ ERROR: Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Get all SQL files sorted by name
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("ℹ️  No SQL migration files found")
        return

    print("=" * 60)
    print("TradLab Migration Runner")
    print("=" * 60)
    print(f"Database: {db_url.split('@')[-1]}")
    print(f"Migrations: {len(sql_files)} files found")
    print("=" * 60)

    # Connect to database
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database: {e}")
        sys.exit(1)

    # Run each migration
    success_count = 0
    error_count = 0

    for sql_file in sql_files:
        print(f"\n📄 Running: {sql_file.name}")
        try:
            sql_content = sql_file.read_text(encoding="utf-8")
            cursor.execute(sql_content)
            print(f"   ✅ Applied successfully")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1

    # Close connection
    cursor.close()
    conn.close()

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {error_count}")
    print("=" * 60)

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
