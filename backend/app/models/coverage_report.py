from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Integer, Numeric, ForeignKey, TIMESTAMP, text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class CoverageReport(Base):
    __tablename__ = "coverage_reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    session_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), unique=True, nullable=False)
    coverage_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), server_default=text("0.00"), nullable=False)
    topics_covered: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)
    topics_missed: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"), nullable=False)

    # Audit & Soft Delete Columns
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    lecture_session: Mapped["LectureSession"] = relationship("LectureSession", back_populates="coverage_report")
