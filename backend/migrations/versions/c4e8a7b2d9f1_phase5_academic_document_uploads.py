"""Phase 5 Academic Document Upload Foundation

Revision ID: c4e8a7b2d9f1
Revises: de90817c6e44
Create Date: 2026-08-01 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4e8a7b2d9f1"
down_revision: Union[str, Sequence[str], None] = "de90817c6e44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "curricula",
        sa.Column("faculty_id", sa.UUID(), nullable=False),
    )
    op.add_column(
        "curricula",
        sa.Column("title", sa.String(length=255), nullable=False),
    )
    op.add_column(
        "curricula",
        sa.Column("document_type", sa.String(length=50), nullable=False),
    )
    op.add_column(
        "curricula",
        sa.Column("description", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "curricula",
        sa.Column("file_name", sa.String(length=255), nullable=False),
    )
    op.add_column(
        "curricula",
        sa.Column("file_path", sa.String(length=512), nullable=False),
    )
    op.add_column(
        "curricula",
        sa.Column("file_size", sa.Integer(), nullable=False),
    )
    op.add_column(
        "curricula",
        sa.Column(
            "processing_status",
            sa.String(length=30),
            server_default=sa.text("'UPLOADED'"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_curricula_faculty_id_faculty",
        "curricula",
        "faculty",
        ["faculty_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.add_column(
        "reference_materials",
        sa.Column("faculty_id", sa.UUID(), nullable=False),
    )
    op.add_column(
        "reference_materials",
        sa.Column("document_type", sa.String(length=50), nullable=False),
    )
    op.add_column(
        "reference_materials",
        sa.Column("description", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "reference_materials",
        sa.Column("file_name", sa.String(length=255), nullable=False),
    )
    op.add_column(
        "reference_materials",
        sa.Column("file_size", sa.Integer(), nullable=False),
    )
    op.add_column(
        "reference_materials",
        sa.Column(
            "processing_status",
            sa.String(length=30),
            server_default=sa.text("'UPLOADED'"),
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_reference_materials_faculty_id_faculty",
        "reference_materials",
        "faculty",
        ["faculty_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_reference_materials_faculty_id_faculty", "reference_materials", type_="foreignkey")
    op.drop_column("reference_materials", "processing_status")
    op.drop_column("reference_materials", "file_size")
    op.drop_column("reference_materials", "file_name")
    op.drop_column("reference_materials", "description")
    op.drop_column("reference_materials", "document_type")
    op.drop_column("reference_materials", "faculty_id")

    op.drop_constraint("fk_curricula_faculty_id_faculty", "curricula", type_="foreignkey")
    op.drop_column("curricula", "processing_status")
    op.drop_column("curricula", "file_size")
    op.drop_column("curricula", "file_path")
    op.drop_column("curricula", "file_name")
    op.drop_column("curricula", "description")
    op.drop_column("curricula", "document_type")
    op.drop_column("curricula", "title")
    op.drop_column("curricula", "faculty_id")
