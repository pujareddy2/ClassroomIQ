from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class CoverageDetail(Base):
    __tablename__ = "coverage_details"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    coverage_result_id: Mapped[UUID] = mapped_column(ForeignKey("coverage_results.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    speaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="Faculty")
    text_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")

    # Relationships
    coverage_result: Mapped["CoverageResult"] = relationship("CoverageResult", back_populates="details")
