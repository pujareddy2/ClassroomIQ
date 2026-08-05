from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class TranscriptTopicMapping(Base):
    __tablename__ = "transcript_topic_mappings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)
    transcript_id: Mapped[UUID] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[UUID] = mapped_column(ForeignKey("transcript_chunks.id", ondelete="CASCADE"), nullable=False)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    chapter_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    topic_id: Mapped[UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    mapping_reason: Mapped[str] = mapped_column(String(255), nullable=False)

    # Audit Columns
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    chunk: Mapped["TranscriptChunk"] = relationship("TranscriptChunk", back_populates="topic_mappings")
