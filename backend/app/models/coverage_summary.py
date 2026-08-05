from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, Float, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class CoverageSummary(Base):
    __tablename__ = "coverage_summaries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    validation_summary_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("validation_summaries.id", ondelete="SET NULL"), nullable=True)

    total_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    covered_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partially_covered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rushed_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    over_explained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repeated_topics: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_scheduled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    raw_coverage_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    weighted_coverage_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    remaining_topics_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sequence_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    processing_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
