from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_institution_department_code"),
    )

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="departments")
    faculty: Mapped[List["Faculty"]] = relationship("Faculty", back_populates="department")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="department")
