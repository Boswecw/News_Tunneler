"""add_ml_models_table

Revision ID: 0a1fd3096f0b
Revises: 004
Create Date: 2025-10-28 23:58:05.031030

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '0a1fd3096f0b'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists using cross-database compatible method
    conn = op.get_bind()
    inspector = inspect(conn)
    table_exists = inspector.has_table('ml_models')

    if not table_exists:
        # Create ml_models table
        op.create_table(
            'ml_models',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(), nullable=False),
            sa.Column('model_type', sa.String(), nullable=False),
            sa.Column('model_path', sa.String(), nullable=False),
            sa.Column('metrics', sa.JSON(), nullable=False),
            sa.Column('feature_importance', sa.JSON(), nullable=True),
            sa.Column('hyperparameters', sa.JSON(), nullable=True),
            sa.Column('training_samples', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes
        op.create_index('ix_ml_models_version', 'ml_models', ['version'], unique=True)
        op.create_index('ix_ml_models_model_type', 'ml_models', ['model_type'])
        op.create_index('ix_ml_models_is_active', 'ml_models', ['is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_ml_models_is_active', table_name='ml_models')
    op.drop_index('ix_ml_models_model_type', table_name='ml_models')
    op.drop_index('ix_ml_models_version', table_name='ml_models')

    # Drop table
    op.drop_table('ml_models')

