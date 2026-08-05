"""
ReferenceRepository — all DB operations for reference material domain.

Extends BaseRepository for shared course/faculty/term helpers.
Adds list_references(), get_reference_by_id(), and soft_delete_reference()
for new API endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.reference_material import ReferenceMaterial
from app.repositories.base_repository import BaseRepository
from app.schemas.pagination import PaginationMeta, make_pagination_meta


class ReferenceRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    # ── Single Record Lookups ─────────────────────────────────────────────────

    def get_reference_by_id(self, reference_id: UUID) -> ReferenceMaterial | None:
        ref = self.db.get(ReferenceMaterial, reference_id)
        if ref is None or ref.status == "DELETED":
            return None
        return ref

    # ── List & Pagination ─────────────────────────────────────────────────────

    def list_references(
        self,
        page: int = 1,
        page_size: int = 20,
        course_id: UUID | None = None,
        document_type: str | None = None,
        faculty_id: UUID | None = None,
        status: str = "ACTIVE",
    ) -> tuple[list[ReferenceMaterial], PaginationMeta]:
        """Return a paginated list of reference materials with optional filters."""
        stmt = select(ReferenceMaterial).where(ReferenceMaterial.status == status)

        if course_id is not None:
            stmt = stmt.where(ReferenceMaterial.course_id == course_id)
        if faculty_id is not None:
            stmt = stmt.where(ReferenceMaterial.faculty_id == faculty_id)
        if document_type is not None:
            stmt = stmt.where(ReferenceMaterial.document_type == document_type.upper())

        # Count total before paginating
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_items = int(self.db.execute(count_stmt).scalar_one())

        # Apply ordering + pagination
        stmt = stmt.order_by(ReferenceMaterial.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())

        return items, make_pagination_meta(page, page_size, total_items)

    # ── Soft Delete ───────────────────────────────────────────────────────────

    def soft_delete_reference(self, reference_id: UUID) -> ReferenceMaterial | None:
        """Set status=DELETED and deleted_at=now() — does NOT physically remove the row."""
        ref = self.db.get(ReferenceMaterial, reference_id)
        if ref is None or ref.status == "DELETED":
            return None
        ref.status = "DELETED"
        ref.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return ref

    # ── Write ─────────────────────────────────────────────────────────────────

    def create_reference_material(self, reference_material: ReferenceMaterial) -> ReferenceMaterial:
        self.db.add(reference_material)
        self.db.flush()
        self.db.refresh(reference_material)
        return reference_material
