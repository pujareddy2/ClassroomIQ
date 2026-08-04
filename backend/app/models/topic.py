from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    parent_topic_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_hours: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    curriculum: Mapped["Curriculum"] = relationship("Curriculum", back_populates="topics")
    parent_topic: Mapped[Optional["Topic"]] = relationship("Topic", remote_side=[id], back_populates="subtopics")
    subtopics: Mapped[List["Topic"]] = relationship("Topic", back_populates="parent_topic")
    topic_references: Mapped[List["TopicReference"]] = relationship("TopicReference", back_populates="topic", cascade="all, delete-orphan")
    transcript_segments: Mapped[List["TranscriptSegment"]] = relationship("TranscriptSegment", back_populates="topic")
