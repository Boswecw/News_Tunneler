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
    
    # 1. Partial index for high-score signals (most frequently queried)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_high_score
        ON signals (score DESC, created_at DESC)
        WHERE score >= 50.0
    """)

    # 2. Partial index for recent signals (last 7 days)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_recent
        ON signals (created_at DESC, score DESC)
        WHERE created_at >= NOW() - INTERVAL '7 days'
    """)

    # 3. Composite index for symbol + timestamp queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_symbol_t
        ON signals (symbol, t DESC)
    """)

    # 4. Index for label-based queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_label_score
        ON signals (label, score DESC)
    """)

    # 5. GIN index for features JSONB column
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_features_gin
        ON signals USING GIN (features)
    """)

    # 6. GIN index for reasons JSONB column
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_reasons_gin
        ON signals USING GIN (reasons)
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
    op.execute("DROP INDEX IF EXISTS idx_signals_high_score")
    op.execute("DROP INDEX IF EXISTS idx_signals_recent")
    op.execute("DROP INDEX IF EXISTS idx_signals_symbol_t")
    op.execute("DROP INDEX IF EXISTS idx_signals_label_score")
    op.execute("DROP INDEX IF EXISTS idx_signals_features_gin")
    op.execute("DROP INDEX IF EXISTS idx_signals_reasons_gin")
    op.execute("DROP INDEX IF EXISTS idx_articles_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_articles_title_trgm")
    op.execute("DROP INDEX IF EXISTS idx_sources_active")

    print("PostgreSQL-specific indexes removed successfully")

