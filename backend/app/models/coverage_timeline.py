from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class CoverageTimeline(Base):
    __tablename__ = "coverage_timelines"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)

    start_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="COVERED")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
