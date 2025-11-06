"""Merge JSONB and users heads

Revision ID: 9f3c0e04fff6
Revises: 8c0e3c708fa1, 53119d0e1c99
Create Date: 2025-02-17 20:30:00.000000

This merge reconciles the branch created by the JSONB migration with the
users table migration so Alembic sees a single head revision again.
"""

# revision identifiers, used by Alembic.
revision = "9f3c0e04fff6"
down_revision = ("8c0e3c708fa1", "53119d0e1c99")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge; real work was already done in the parent revisions.
    pass


def downgrade() -> None:
    # This merge introduced no schema changes to undo.
    pass
