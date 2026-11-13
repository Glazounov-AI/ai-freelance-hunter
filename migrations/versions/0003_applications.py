"""Human-reviewed applications and audit trail.

Revision ID: 0003_applications
Revises: 0002_ai_analysis
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_applications"
down_revision: str | None = "0002_ai_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("opportunity_id", sa.Integer(), sa.ForeignKey(
            "opportunities.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey(
            "opportunity_analyses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("draft", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "APPROVED", "REJECTED", name="application_status",
                                     native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "application_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey(
            "applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("note", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("application_id", "sequence", name="uq_application_event_sequence"),
    )
    op.create_index("ix_application_events_application_id", "application_events", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_application_events_application_id", table_name="application_events")
    op.drop_table("application_events")
    op.drop_table("applications")
