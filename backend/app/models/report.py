from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    faculty_id: Mapped[UUID] = mapped_column(ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False)
    session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="SET NULL"), nullable=True)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="reports")
    lecture_session: Mapped[Optional["LectureSession"]] = relationship("LectureSession", back_populates="reports")
