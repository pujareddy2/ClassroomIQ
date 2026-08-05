from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    transcript_id: Mapped[UUID] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    sentence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit Columns — Python-side defaults so they are never NULL
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="chunks")
    topic_mappings: Mapped[List["TranscriptTopicMapping"]] = relationship(
        "TranscriptTopicMapping", back_populates="chunk", cascade="all, delete-orphan"
    )
