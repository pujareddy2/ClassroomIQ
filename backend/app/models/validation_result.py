from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Float, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    chunk_id: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_start_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    chunk_end_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    speaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="Faculty")

    category: Mapped[str] = mapped_column(String(50), nullable=False, default="CONCEPT")
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="CORRECT")
    validation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="CORRECT")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    evidence_list: Mapped[List["ValidationEvidence"]] = relationship(
        "ValidationEvidence", back_populates="validation_result", cascade="all, delete-orphan"
    )
