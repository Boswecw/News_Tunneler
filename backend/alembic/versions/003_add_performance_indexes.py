"""Add performance indexes

Revision ID: 003
Revises: 002
Create Date: 2025-10-29

Phase 1 Improvement: Database indexing strategy for faster queries
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes."""

    # Use raw SQL to create indexes with IF NOT EXISTS (SQLite 3.32+)
    # This makes the migration idempotent

    conn = op.get_bind()

    # Helper function to check if table exists
    def table_exists(table_name):
        result = conn.execute(sa.text(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        ))
        return result.fetchone() is not None

    # Composite index for articles by published date and ticker
    if table_exists('articles'):
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_published_ticker
            ON articles (published_at, ticker_guess)
        """))

        # Index on source URL for articles
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_articles_url
            ON articles (url)
        """))

    # Composite index for scores by total and computed time
    if table_exists('scores'):
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_scores_total_computed
            ON scores (total, computed_at)
        """))

        # Index on article_id for scores (foreign key)
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_scores_article_id
            ON scores (article_id)
        """))

    # Composite index for signals by score and timestamp
    if table_exists('signals'):
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_score_t
            ON signals (score, t)
        """))

        # Index on signal label for ML training queries
        conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_signals_label
            ON signals (label)
        """))


def downgrade():
    """Remove performance indexes."""

    conn = op.get_bind()

    # Drop all indexes in reverse order
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_signals_label"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_signals_score_t"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_scores_article_id"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_scores_total_computed"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_url"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_published_ticker"))

