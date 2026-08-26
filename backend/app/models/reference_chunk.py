from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Text, ForeignKey, TIMESTAMP, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class ReferenceChunk(Base):
    __tablename__ = "reference_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    reference_material_id: Mapped[UUID] = mapped_column(ForeignKey("reference_materials.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Vector embedding stored as JSON list of float values
    embedding: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Audit & Status Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)

    # Relationships
    reference_material: Mapped["ReferenceMaterial"] = relationship("ReferenceMaterial", back_populates="chunks")
    course: Mapped["Course"] = relationship("Course")
