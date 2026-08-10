from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    flag_id: Mapped[UUID] = mapped_column(ForeignKey("validation_flags.id", ondelete="CASCADE"), unique=True, nullable=False)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. APPROVED, REJECTED
    reviewer_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    # Explicitly specify foreign_keys to disambiguate reviewer_id vs created_by (both -> users)
    validation_flag: Mapped["ValidationFlag"] = relationship(
        "ValidationFlag",
        back_populates="review_decision",
        foreign_keys=[flag_id],
    )
    reviewer: Mapped["User"] = relationship(
        "User",
        back_populates="review_decisions",
        foreign_keys=[reviewer_id],
    )
