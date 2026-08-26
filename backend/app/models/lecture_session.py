from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Date, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class LectureSession(Base):
    __tablename__ = "lecture_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False)
    faculty_id: Mapped[UUID] = mapped_column(ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    lecture_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    classroom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="lecture_sessions")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="lecture_sessions")
    recording: Mapped[Optional["Recording"]] = relationship("Recording", back_populates="lecture_session", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="lecture_session")
