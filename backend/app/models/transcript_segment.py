from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, Float, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    transcript_id: Mapped[UUID] = mapped_column(ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="transcript_segments")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="transcript_segments")
    validation_flags: Mapped[List["ValidationFlag"]] = relationship("ValidationFlag", back_populates="transcript_segment", cascade="all, delete-orphan")
