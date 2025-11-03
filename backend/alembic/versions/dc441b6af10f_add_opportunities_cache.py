"""add_opportunities_cache

Revision ID: dc441b6af10f
Revises: 383a6b19491c
Create Date: 2025-10-30 21:18:48.740058

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'dc441b6af10f'
down_revision = '383a6b19491c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists using cross-database compatible method
    conn = op.get_bind()
    inspector = inspect(conn)
    table_exists = inspector.has_table('opportunities_cache')

    if not table_exists:
        # Create opportunities_cache table
        op.create_table(
            'opportunities_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('symbol', sa.String(10), nullable=False),
            sa.Column('composite_score', sa.Float(), nullable=False),
            sa.Column('signal_score', sa.Float(), nullable=True),
            sa.Column('llm_confidence', sa.Float(), nullable=True),
            sa.Column('llm_stance', sa.String(20), nullable=True),
            sa.Column('ml_confidence', sa.Float(), nullable=True),
            sa.Column('model_r2', sa.Float(), nullable=True),
            sa.Column('model_trained', sa.Boolean(), nullable=True),
            sa.Column('model_mode', sa.String(10), nullable=True),
            sa.Column('article_id', sa.Integer(), nullable=True),
            sa.Column('article_title', sa.String(500), nullable=True),
            sa.Column('signal_timestamp', sa.Float(), nullable=True),
            sa.Column('cached_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes for fast lookups
        op.create_index('idx_opportunities_expires_at', 'opportunities_cache', ['expires_at'])
        op.create_index('idx_opportunities_symbol', 'opportunities_cache', ['symbol'])
        op.create_index('idx_opportunities_score', 'opportunities_cache', ['composite_score'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_opportunities_score', table_name='opportunities_cache')
    op.drop_index('idx_opportunities_symbol', table_name='opportunities_cache')
    op.drop_index('idx_opportunities_expires_at', table_name='opportunities_cache')

    # Drop table
    op.drop_table('opportunities_cache')

