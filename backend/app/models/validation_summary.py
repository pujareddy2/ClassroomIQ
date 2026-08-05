from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import Integer, Float, ForeignKey, TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class ValidationSummary(Base):
    __tablename__ = "validation_summaries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)

    validated_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_concepts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incorrect_concepts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    formula_issues: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    code_issues: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_concepts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    terminology_errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Added Quality & Analytics Metrics
    overall_validation_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    lecture_quality: Mapped[str] = mapped_column(String(50), nullable=False, default="EXCELLENT")
    validation_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    processing_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
