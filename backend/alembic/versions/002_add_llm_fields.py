"""Add LLM analysis fields to articles

Revision ID: 002
Revises: 001
Create Date: 2025-10-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add LLM analysis fields to articles table."""
    # Add llm_plan column (JSON)
    op.add_column('articles', sa.Column('llm_plan', sa.JSON(), nullable=True))
    
    # Add strategy_bucket column (String)
    op.add_column('articles', sa.Column('strategy_bucket', sa.String(), nullable=True))
    
    # Add strategy_risk column (JSON)
    op.add_column('articles', sa.Column('strategy_risk', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove LLM analysis fields from articles table."""
    op.drop_column('articles', 'strategy_risk')
    op.drop_column('articles', 'strategy_bucket')
    op.drop_column('articles', 'llm_plan')

