from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class ReferenceMaterial(Base):
    __tablename__ = "reference_materials"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    academic_term_id: Mapped[UUID] = mapped_column(ForeignKey("academic_terms.id", ondelete="RESTRICT"), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    edition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), server_default=text("'UPLOADED'"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="reference_materials")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="reference_materials")
    topic_references: Mapped[List["TopicReference"]] = relationship("TopicReference", back_populates="reference_material", cascade="all, delete-orphan")
    validation_flags: Mapped[List["ValidationFlag"]] = relationship("ValidationFlag", back_populates="reference_material")
