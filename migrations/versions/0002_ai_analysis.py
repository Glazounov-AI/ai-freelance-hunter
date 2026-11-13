"""Store AI analyses and draft proposals.

Revision ID: 0002_ai_analysis
Revises: 0001_foundation
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_ai_analysis"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opportunity_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey(
            "opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("matched_skills_json", sa.Text(), nullable=False),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("draft", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_analysis_score"),
    )
    op.create_index("ix_opportunity_analyses_opportunity_id",
                    "opportunity_analyses", ["opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_analyses_opportunity_id",
                  table_name="opportunity_analyses")
    op.drop_table("opportunity_analyses")
