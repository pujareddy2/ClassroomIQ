from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Course(Base):
    __tablename__ = "courses"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    course_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=3, server_default=text("3"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="courses")
    curricula: Mapped[List["Curriculum"]] = relationship("Curriculum", back_populates="course", cascade="all, delete-orphan")
    reference_materials: Mapped[List["ReferenceMaterial"]] = relationship("ReferenceMaterial", back_populates="course", cascade="all, delete-orphan")
    lecture_sessions: Mapped[List["LectureSession"]] = relationship("LectureSession", back_populates="course")
