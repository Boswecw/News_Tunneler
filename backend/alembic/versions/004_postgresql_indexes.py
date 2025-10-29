"""Add PostgreSQL-specific indexes

Revision ID: 004
Revises: 003
Create Date: 2025-10-29

PostgreSQL-specific optimizations:
- GIN indexes for full-text search
- Partial indexes for filtered queries
- JSONB indexes for LLM plan data
- Trigram indexes for fuzzy text search
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add PostgreSQL-specific indexes."""
    # Get connection to check database type
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    # Only apply PostgreSQL-specific indexes if using PostgreSQL
    if dialect_name != 'postgresql':
        print(f"Skipping PostgreSQL-specific indexes (current dialect: {dialect_name})")
        return
    
    print("Applying PostgreSQL-specific indexes...")
    
    # Enable required extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")
    
    # 1. Full-text search index on signals (title + content)
    # Create tsvector column for full-text search
    op.execute("""
        ALTER TABLE signals 
        ADD COLUMN IF NOT EXISTS search_vector tsvector 
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(content, '')), 'B')
        ) STORED
    """)
    
    # Create GIN index on search vector
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_search_vector 
        ON signals USING GIN (search_vector)
    """)
    
    # 2. Trigram index for fuzzy text search on title
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_title_trgm 
        ON signals USING GIN (title gin_trgm_ops)
    """)
    
    # 3. Partial index for high-score signals (most frequently queried)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_high_score 
        ON signals (total_score DESC, created_at DESC) 
        WHERE total_score >= 10.0
    """)
    
    # 4. Partial index for recent signals (last 7 days)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_recent 
        ON signals (created_at DESC, total_score DESC) 
        WHERE created_at >= NOW() - INTERVAL '7 days'
    """)
    
    # 5. Composite index for ticker + date range queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_ticker_date 
        ON signals (ticker, created_at DESC) 
        WHERE ticker IS NOT NULL
    """)
    
    # 6. GIN index for multi-column searches (ticker + score + date)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_composite_gin 
        ON signals USING GIN (ticker, total_score, created_at)
    """)
    
    # 7. Index for source-based queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_source_date 
        ON signals (source, created_at DESC)
    """)
    
    # 8. Partial index for analyzed signals (has LLM scores)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_analyzed 
        ON signals (created_at DESC) 
        WHERE catalyst_score > 0 OR novelty_score > 0 OR credibility_score > 0
    """)
    
    # Articles table indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_search_vector 
        ON articles USING GIN (
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''))
        )
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_title_trgm 
        ON articles USING GIN (title gin_trgm_ops)
    """)
    
    # Sources table indexes
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_sources_active 
        ON sources (active, name) 
        WHERE active = true
    """)
    
    print("PostgreSQL-specific indexes created successfully")


def downgrade() -> None:
    """Remove PostgreSQL-specific indexes."""
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    if dialect_name != 'postgresql':
        print(f"Skipping PostgreSQL index removal (current dialect: {dialect_name})")
        return
    
    print("Removing PostgreSQL-specific indexes...")
    
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_signals_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_signals_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_signals_high_score")
    op.execute("DROP INDEX IF EXISTS idx_signals_recent")
    op.execute("DROP INDEX IF EXISTS idx_signals_ticker_date")
    op.execute("DROP INDEX IF EXISTS idx_signals_composite_gin")
    op.execute("DROP INDEX IF EXISTS idx_signals_source_date")
    op.execute("DROP INDEX IF EXISTS idx_signals_analyzed")
    op.execute("DROP INDEX IF EXISTS idx_articles_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_articles_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_sources_active")
    
    # Drop search_vector column
    op.execute("ALTER TABLE signals DROP COLUMN IF EXISTS search_vector")
    
    print("PostgreSQL-specific indexes removed successfully")

