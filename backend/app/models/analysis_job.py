"""Persisted execution state for the Member 2 AI analysis pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    current_stage: Mapped[str] = mapped_column(String(40), nullable=False, default="QUEUED")
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    coverage_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    teaching_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    recommendation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    explainability_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    progress_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
