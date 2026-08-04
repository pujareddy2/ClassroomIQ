from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Numeric, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class ValidationFlag(Base):
    __tablename__ = "validation_flags"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    segment_id: Mapped[UUID] = mapped_column(ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False)
    reference_material_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("reference_materials.id", ondelete="SET NULL"), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    ai_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    transcript_segment: Mapped["TranscriptSegment"] = relationship("TranscriptSegment", back_populates="validation_flags")
    reference_material: Mapped[Optional["ReferenceMaterial"]] = relationship("ReferenceMaterial", back_populates="validation_flags")
    review_decision: Mapped[Optional["ReviewDecision"]] = relationship("ReviewDecision", back_populates="validation_flag", cascade="all, delete-orphan")
