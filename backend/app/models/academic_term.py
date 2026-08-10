from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Date, ForeignKey, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class AcademicTerm(Base):
    __tablename__ = "academic_terms"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    semester: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("institution_id", "academic_year", "semester", name="uq_institution_academic_term"),
    )

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="academic_terms")
    curricula: Mapped[List["Curriculum"]] = relationship("Curriculum", back_populates="academic_term", cascade="all, delete-orphan")
