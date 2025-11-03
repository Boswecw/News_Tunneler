"""
Apply PostgreSQL-specific indexes manually

This script applies the PostgreSQL-specific indexes from migration 004
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variable to use PostgreSQL
os.environ['USE_POSTGRESQL'] = 'true'

from app.core.db import engine
import sqlalchemy as sa

print("=" * 60)
print("APPLYING POSTGRESQL-SPECIFIC INDEXES")
print("=" * 60)
print()

# Check if we're using PostgreSQL
if engine.dialect.name != 'postgresql':
    print(f"✗ Not using PostgreSQL (current dialect: {engine.dialect.name})")
    print("  Set USE_POSTGRESQL=true to use PostgreSQL")
    sys.exit(1)

print(f"✓ Using PostgreSQL")
print()

with engine.connect() as conn:
    # Enable required extensions
    print("Enabling PostgreSQL extensions...")
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS btree_gin"))
    conn.commit()
    print("✓ Extensions enabled")
    print()
    
    # 1. Full-text search index on signals (title + content)
    print("Creating full-text search column...")
    try:
        conn.execute(sa.text("""
            ALTER TABLE signals 
            ADD COLUMN IF NOT EXISTS search_vector tsvector 
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(label, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(symbol, '')), 'B')
            ) STORED
        """))
        conn.commit()
        print("✓ Full-text search column created")
    except Exception as e:
        print(f"⚠ Full-text search column: {e}")
    print()
    
    # Create GIN index on search vector
    print("Creating GIN index on search vector...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_search_vector 
            ON signals USING GIN (search_vector)
        """))
        conn.commit()
        print("✓ GIN index created")
    except Exception as e:
        print(f"⚠ GIN index: {e}")
    print()
    
    # 2. Trigram index for fuzzy text search on symbol
    print("Creating trigram index on symbol...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_symbol_trgm 
            ON signals USING GIN (symbol gin_trgm_ops)
        """))
        conn.commit()
        print("✓ Trigram index created")
    except Exception as e:
        print(f"⚠ Trigram index: {e}")
    print()
    
    # 3. Partial index for high-score signals (most frequently queried)
    print("Creating partial index for high-score signals...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_high_score 
            ON signals (score DESC, created_at DESC) 
            WHERE score >= 10.0
        """))
        conn.commit()
        print("✓ Partial index for high scores created")
    except Exception as e:
        print(f"⚠ Partial index for high scores: {e}")
    print()
    
    # 4. Partial index for recent signals (last 7 days)
    print("Creating partial index for recent signals...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_recent 
            ON signals (created_at DESC, score DESC) 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """))
        conn.commit()
        print("✓ Partial index for recent signals created")
    except Exception as e:
        print(f"⚠ Partial index for recent signals: {e}")
    print()
    
    # 5. Composite index for symbol + date range queries
    print("Creating composite index for symbol + date...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_symbol_date 
            ON signals (symbol, created_at DESC) 
            WHERE symbol IS NOT NULL
        """))
        conn.commit()
        print("✓ Composite index created")
    except Exception as e:
        print(f"⚠ Composite index: {e}")
    print()
    
    # 6. GIN index for multi-column searches (symbol + score + date)
    print("Creating GIN index for multi-column searches...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_composite_gin 
            ON signals USING GIN (symbol, score, created_at)
        """))
        conn.commit()
        print("✓ GIN composite index created")
    except Exception as e:
        print(f"⚠ GIN composite index: {e}")
    print()
    
    # Articles table indexes
    print("Creating articles full-text search index...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_search_vector 
            ON articles USING GIN (
                to_tsvector('english', coalesce(title, '') || ' ' || coalesce(summary, ''))
            )
        """))
        conn.commit()
        print("✓ Articles full-text search index created")
    except Exception as e:
        print(f"⚠ Articles full-text search index: {e}")
    print()
    
    print("Creating articles trigram index...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_title_trgm 
            ON articles USING GIN (title gin_trgm_ops)
        """))
        conn.commit()
        print("✓ Articles trigram index created")
    except Exception as e:
        print(f"⚠ Articles trigram index: {e}")
    print()

    print("Ensuring articles LLM plan GIN index...")
    try:
        conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_llm_plan"))
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_llm_plan_gin
            ON articles USING GIN (llm_plan)
        """))
        conn.commit()
        print("✓ Articles LLM plan GIN index ready")
    except Exception as e:
        print(f"⚠ Articles LLM plan index: {e}")
    print()
    
    # Sources table indexes
    print("Creating sources active index...")
    try:
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_sources_active 
            ON sources (enabled, name) 
            WHERE enabled = true
        """))
        conn.commit()
        print("✓ Sources active index created")
    except Exception as e:
        print(f"⚠ Sources active index: {e}")
    print()
    
    # List all indexes
    print("=" * 60)
    print("POSTGRESQL INDEXES SUMMARY")
    print("=" * 60)
    print()
    
    result = conn.execute(sa.text("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname
    """))
    
    indexes_by_table = {}
    for row in result:
        table = row[1]
        index = row[2]
        if table not in indexes_by_table:
            indexes_by_table[table] = []
        indexes_by_table[table].append(index)
    
    for table, indexes in sorted(indexes_by_table.items()):
        print(f"Table: {table}")
        for idx in indexes:
            print(f"  - {idx}")
        print()
    
    total_indexes = sum(len(indexes) for indexes in indexes_by_table.values())
    print(f"Total custom indexes: {total_indexes}")
    print()

print("=" * 60)
print("✓ POSTGRESQL INDEXES APPLIED SUCCESSFULLY!")
print("=" * 60)
