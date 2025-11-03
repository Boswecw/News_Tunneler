"""use_jsonb_for_llm_plan

Revision ID: 8c0e3c708fa1
Revises: dc441b6af10f
Create Date: 2025-02-17 20:00:00.000000

Ensure the llm_plan column uses PostgreSQL jsonb so we can attach a GIN index
without hitting operator-class errors during deploys.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "8c0e3c708fa1"
down_revision = "dc441b6af10f"
branch_labels = None
depends_on = None


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    try:
        return any(col.get("name") == column_name for col in inspector.get_columns(table_name))
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        # JSONB is PostgreSQL-specific; other engines can stay on JSON.
        return

    inspector = inspect(conn)
    if not inspector.has_table("articles"):
        return

    if _column_exists(inspector, "articles", "llm_plan"):
        conn.execute(
            sa.text(
                """
                ALTER TABLE articles
                ALTER COLUMN llm_plan
                TYPE jsonb
                USING llm_plan::jsonb
                """
            )
        )

    if _column_exists(inspector, "articles", "strategy_risk"):
        conn.execute(
            sa.text(
                """
                ALTER TABLE articles
                ALTER COLUMN strategy_risk
                TYPE jsonb
                USING strategy_risk::jsonb
                """
            )
        )

    # Replace any legacy B-tree index with a proper GIN index.
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_llm_plan"))
    conn.execute(
        sa.text(
            """
            CREATE INDEX IF NOT EXISTS idx_articles_llm_plan_gin
            ON articles USING GIN (llm_plan)
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    inspector = inspect(conn)
    if not inspector.has_table("articles"):
        return

    conn.execute(sa.text("DROP INDEX IF EXISTS idx_articles_llm_plan_gin"))

    if _column_exists(inspector, "articles", "llm_plan"):
        conn.execute(
            sa.text(
                """
                ALTER TABLE articles
                ALTER COLUMN llm_plan
                TYPE json
                USING to_json(llm_plan)
                """
            )
        )

    if _column_exists(inspector, "articles", "strategy_risk"):
        conn.execute(
            sa.text(
                """
                ALTER TABLE articles
                ALTER COLUMN strategy_risk
                TYPE json
                USING to_json(strategy_risk)
                """
            )
        )
