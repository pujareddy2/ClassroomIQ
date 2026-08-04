from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Recording(Base):
    __tablename__ = "recordings"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    session_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    lecture_session: Mapped["LectureSession"] = relationship("LectureSession", back_populates="recording")
    transcript: Mapped[Optional["Transcript"]] = relationship("Transcript", back_populates="recording", cascade="all, delete-orphan")
