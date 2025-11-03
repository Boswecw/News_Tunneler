"""add_performance_indexes

Revision ID: 383a6b19491c
Revises: 0a1fd3096f0b
Create Date: 2025-10-30 19:24:56.391018

Additional performance indexes for opportunities endpoint optimization:
- Index on Article.llm_plan for filtering articles with LLM analysis
- Composite index on Signal(symbol, t) for batch queries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '383a6b19491c'
down_revision = '0a1fd3096f0b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add additional performance indexes."""
    conn = op.get_bind()
    inspector = inspect(conn)

    # Helper function to check if table exists using cross-database compatible method
    def table_exists(table_name):
        return inspector.has_table(table_name)

    # Index on Article.llm_plan for filtering articles with LLM analysis
    # This speeds up queries that filter by llm_plan IS NOT NULL
    if table_exists('articles'):
        # SQLite doesn't support partial indexes on JSON columns directly
        # But we can create an index on the column itself
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_llm_plan
            ON articles (llm_plan)
        """))

        # Also add index on published_at for date range queries
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_published_at
            ON articles (published_at)
        """))

    # Composite index on Signal(symbol, t) for batch queries
    # This is critical for the opportunities endpoint batch query optimization
    if table_exists('signals'):
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_symbol_t
            ON signals (symbol, t DESC)
        """))

        # Also add standalone symbol index for lookups
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_symbol
            ON signals (symbol)
        """))


def downgrade() -> None:
    """Remove additional performance indexes."""
    conn = op.get_bind()

    # Drop all indexes in reverse order
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_signals_symbol"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_signals_symbol_t"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_published_at"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_llm_plan"))

