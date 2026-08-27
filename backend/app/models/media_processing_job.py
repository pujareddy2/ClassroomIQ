"""
MediaProcessingJob — Async Job Tracker for Member 1's Audio & Video Pipelines.
Persists job state in PostgreSQL so status survives server restarts and can be polled by the frontend.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MediaProcessingJob(Base):
    """Tracks the status of background audio/video processing tasks."""

    __tablename__ = "media_processing_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "audio_process" | "video_process" | "full_pipeline"
    job_type: Mapped[str] = mapped_column(String(30), nullable=False, default="audio_process")

    # "PENDING" | "RUNNING" | "COMPLETED" | "FAILED"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)

    # 0–100 for UI progress bars
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cached JSON result so GET /transcript doesn't need to re-query
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Human-readable failure reason if status == FAILED
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Configuration snapshot (domain_subject, model_size, etc.)
    config_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<MediaProcessingJob id={self.id} type={self.job_type} status={self.status}>"
