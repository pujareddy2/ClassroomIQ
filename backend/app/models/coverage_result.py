from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Float, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class CoverageResult(Base):
    __tablename__ = "coverage_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)

    coverage_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_SCHEDULED")
    coverage_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    expected_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    actual_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_difference_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    over_explained_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    first_mentioned_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_mentioned_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sequence_order_in_curriculum: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sequence_order_in_lecture: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sequence_integrity_status: Mapped[str] = mapped_column(String(50), nullable=False, default="CORRECT_SEQUENCE")

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    details: Mapped[List["CoverageDetail"]] = relationship(
        "CoverageDetail", back_populates="coverage_result", cascade="all, delete-orphan"
    )
