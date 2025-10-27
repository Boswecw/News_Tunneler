"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('last_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
    )
    op.create_index('idx_source_enabled', 'sources', ['enabled'])
    op.create_index('idx_source_url', 'sources', ['url'])

    # Create articles table
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=False),
        sa.Column('ticker_guess', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
    )
    op.create_index('idx_article_published_at', 'articles', ['published_at'])
    op.create_index('idx_article_ticker_guess', 'articles', ['ticker_guess'])
    op.create_index('idx_article_url', 'articles', ['url'])

    # Create scores table
    op.create_table(
        'scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('catalyst', sa.Float(), nullable=False),
        sa.Column('novelty', sa.Float(), nullable=False),
        sa.Column('credibility', sa.Float(), nullable=False),
        sa.Column('sentiment', sa.Float(), nullable=False),
        sa.Column('liquidity', sa.Float(), nullable=False),
        sa.Column('total', sa.Float(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id'),
    )
    op.create_index('idx_score_total', 'scores', ['total'])
    op.create_index('idx_score_article_id', 'scores', ['article_id'])

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('weight_catalyst', sa.Float(), nullable=False),
        sa.Column('weight_novelty', sa.Float(), nullable=False),
        sa.Column('weight_credibility', sa.Float(), nullable=False),
        sa.Column('weight_sentiment', sa.Float(), nullable=False),
        sa.Column('weight_liquidity', sa.Float(), nullable=False),
        sa.Column('min_alert_score', sa.Float(), nullable=False),
        sa.Column('poll_interval_sec', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_type', sa.String(), nullable=False),
        sa.Column('target', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('webhooks')
    op.drop_table('settings')
    op.drop_table('scores')
    op.drop_table('articles')
    op.drop_table('sources')

