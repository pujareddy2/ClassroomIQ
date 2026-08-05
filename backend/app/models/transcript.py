from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Text, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    lecture_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=True)
    recording_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("recordings.id", ondelete="CASCADE"), unique=True, nullable=True)
    language: Mapped[str] = mapped_column(String(50), default="en", server_default=text("'en'"), nullable=False)
    total_words: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    recording: Mapped[Optional["Recording"]] = relationship("Recording", back_populates="transcript")
    transcript_segments: Mapped[List["TranscriptSegment"]] = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan")
    chunks: Mapped[List["TranscriptChunk"]] = relationship("TranscriptChunk", back_populates="transcript", cascade="all, delete-orphan")
