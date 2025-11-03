"""Add performance indexes (cross-DB)

Revision ID: 003
Revises: 002
Create Date: 2025-10-29

Phase 1 Improvement: Database indexing strategy for faster queries
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    return inspect(conn).has_table(table_name)


def _index_exists(conn, table_name: str, index_name: str) -> bool:
    insp = inspect(conn)
    if not _table_exists(conn, table_name):
        return False
    try:
        indexes = insp.get_indexes(table_name)
    except Exception:
        return False
    return any(ix.get("name") == index_name for ix in indexes)


def _safe_create_index(name: str, table: str, cols: list[str], unique: bool = False):
    bind = op.get_bind()
    if not _table_exists(bind, table):
        return
    if not _index_exists(bind, table, name):
        op.create_index(name, table, cols, unique=unique)


def _safe_drop_index(name: str, table: str):
    # Drop if present; ignore if missing
    try:
        op.drop_index(name, table_name=table)
    except Exception:
        pass


def upgrade():
    # articles
    _safe_create_index(
        name="idx_articles_published_ticker",
        table="articles",
        cols=["published_at", "ticker_guess"],
        unique=False,
    )
    _safe_create_index(
        name="idx_articles_url",
        table="articles",
        cols=["url"],
        unique=False,
    )

    # scores
    _safe_create_index(
        name="idx_scores_total_computed",
        table="scores",
        cols=["total", "computed_at"],
        unique=False,
    )
    _safe_create_index(
        name="idx_scores_article_id",
        table="scores",
        cols=["article_id"],
        unique=False,
    )

    # signals
    _safe_create_index(
        name="idx_signals_score_t",
        table="signals",
        cols=["score", "t"],   # ensure column 't' really exists (timestamp?)
        unique=False,
    )
    _safe_create_index(
        name="idx_signals_label",
        table="signals",
        cols=["label"],
        unique=False,
    )


def downgrade():
    _safe_drop_index("idx_signals_label", "signals")
    _safe_drop_index("idx_signals_score_t", "signals")
    _safe_drop_index("idx_scores_article_id", "scores")
    _safe_drop_index("idx_scores_total_computed", "scores")
    _safe_drop_index("idx_articles_url", "articles")
    _safe_drop_index("idx_articles_published_ticker", "articles")
