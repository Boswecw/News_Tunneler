"""
Migration script to add article_id and confidence columns to signals table.
Run this once to update the database schema.
"""
import sqlite3
import sys
from pathlib import Path

# Get database path
db_path = Path(__file__).parent / "data" / "news.db"

if not db_path.exists():
    print(f"❌ Database not found at {db_path}")
    sys.exit(1)

print(f"📊 Migrating database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(signals)")
    columns = {row[1] for row in cursor.fetchall()}
    
    changes_made = False
    
    # Add article_id column if it doesn't exist
    if "article_id" not in columns:
        print("➕ Adding article_id column...")
        cursor.execute("ALTER TABLE signals ADD COLUMN article_id INTEGER")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_signals_article_id ON signals (article_id)")
        changes_made = True
        print("✅ Added article_id column")
    else:
        print("✓ article_id column already exists")
    
    # Add confidence column if it doesn't exist
    if "confidence" not in columns:
        print("➕ Adding confidence column...")
        cursor.execute("ALTER TABLE signals ADD COLUMN confidence FLOAT")
        changes_made = True
        print("✅ Added confidence column")
    else:
        print("✓ confidence column already exists")
    
    if changes_made:
        conn.commit()
        print("\n✅ Migration completed successfully!")
    else:
        print("\n✓ No migration needed - schema is up to date")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Migration failed: {e}")
    sys.exit(1)
finally:
    conn.close()

