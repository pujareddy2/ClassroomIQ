from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    # Explicitly specify foreign_keys to disambiguate user_id vs created_by (both -> users)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="faculty",
        foreign_keys=[user_id],
    )
    department: Mapped["Department"] = relationship("Department", back_populates="faculty")
    curriculum_documents: Mapped[List["Curriculum"]] = relationship("Curriculum", back_populates="faculty")
    reference_materials: Mapped[List["ReferenceMaterial"]] = relationship("ReferenceMaterial", back_populates="faculty")
    lecture_sessions: Mapped[List["LectureSession"]] = relationship("LectureSession", back_populates="faculty")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="faculty")
