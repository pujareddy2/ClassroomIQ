"""Add durable AI analysis execution jobs.

Revision ID: a1b2c3d4e5f6
Revises: 999976ba9345
"""

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "999976ba9345"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("lecture_id", sa.UUID(), nullable=False),
        sa.Column("curriculum_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_stage", sa.String(length=40), nullable=False),
        sa.Column("validation_status", sa.String(length=20), nullable=False),
        sa.Column("coverage_status", sa.String(length=20), nullable=False),
        sa.Column("teaching_status", sa.String(length=20), nullable=False),
        sa.Column("recommendation_status", sa.String(length=20), nullable=False),
        sa.Column("explainability_status", sa.String(length=20), nullable=False),
        sa.Column("progress_percentage", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lecture_id"], ["lecture_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_jobs_lecture_id", "analysis_jobs", ["lecture_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_lecture_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
