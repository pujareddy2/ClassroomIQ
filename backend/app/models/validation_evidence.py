from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class ValidationEvidence(Base):
    __tablename__ = "validation_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    validation_result_id: Mapped[UUID] = mapped_column(ForeignKey("validation_results.id", ondelete="CASCADE"), nullable=False)
    reference_material_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("reference_materials.id", ondelete="SET NULL"), nullable=True)

    reference_document: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reference_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    curriculum_topic: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    validation_result: Mapped["ValidationResult"] = relationship("ValidationResult", back_populates="evidence_list")
    reference_material: Mapped[Optional["ReferenceMaterial"]] = relationship("ReferenceMaterial")
