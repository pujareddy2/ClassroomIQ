"""
ORM Models for the Recommendation Engine.

Tables:
  rec_analyses           — idempotency record per lecture
  rec_items              — individual recommendation records
  rec_evidence           — supporting evidence per recommendation
  rec_priority           — priority metadata per recommendation
  rec_weekly             — weekly summary per faculty
  rec_monthly            — monthly summary per faculty
  rec_summary            — high-level per-lecture summary
"""

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Boolean, Float, ForeignKey, Integer, JSON, String, Text, TIMESTAMP,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── 1. Analysis Record (idempotency) ──────────────────────────────────────────

class RecAnalysis(Base):
    """One active analysis per lecture. Tracks the prerequisite hash for idempotency."""

    __tablename__ = "rec_analyses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False
    )
    faculty_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True
    )
    curriculum_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("curricula.id", ondelete="SET NULL"), nullable=True
    )
    coverage_summary_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("coverage_summaries.id", ondelete="SET NULL"), nullable=True
    )
    validation_summary_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("validation_summaries.id", ondelete="SET NULL"), nullable=True
    )
    teaching_summary_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("teaching_summary.id", ondelete="SET NULL"), nullable=True
    )

    # Idempotency
    prerequisite_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    regeneration_trigger: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Counts
    total_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    informational_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    processing_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationships
    items: Mapped[List["RecItem"]] = relationship(
        "RecItem", back_populates="analysis", cascade="all, delete-orphan"
    )
    summary: Mapped[Optional["RecSummary"]] = relationship(
        "RecSummary", back_populates="analysis", cascade="all, delete-orphan", uselist=False
    )


# ── 2. Recommendation Item ────────────────────────────────────────────────────

class RecItem(Base):
    """A single recommendation produced by the Rule Engine + LLM writer."""

    __tablename__ = "rec_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("rec_analyses.id", ondelete="CASCADE"), nullable=False
    )
    lecture_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Classification
    category: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g. Coverage, Validation, Pedagogical
    recommendation_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Content
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    raw_reason: Mapped[str] = mapped_column(Text, nullable=False)  # pre-LLM rule output

    # Scores
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    urgency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")

    # Merging
    merged_from: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # source categories merged

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationships
    analysis: Mapped["RecAnalysis"] = relationship("RecAnalysis", back_populates="items")
    evidence: Mapped[List["RecEvidence"]] = relationship(
        "RecEvidence", back_populates="item", cascade="all, delete-orphan"
    )
    priority: Mapped[Optional["RecPriority"]] = relationship(
        "RecPriority", back_populates="item", cascade="all, delete-orphan", uselist=False
    )


# ── 3. Supporting Evidence ────────────────────────────────────────────────────

class RecEvidence(Base):
    """One piece of supporting evidence attached to a recommendation item."""

    __tablename__ = "rec_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(
        ForeignKey("rec_items.id", ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)      # "coverage" | "validation" | "teaching"
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "SKIPPED_TOPIC"
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metric_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    topic_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationship
    item: Mapped["RecItem"] = relationship("RecItem", back_populates="evidence")


# ── 4. Priority Record ────────────────────────────────────────────────────────

class RecPriority(Base):
    """Detailed priority breakdown for a recommendation item."""

    __tablename__ = "rec_priority"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(
        ForeignKey("rec_items.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    urgency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    frequency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationship
    item: Mapped["RecItem"] = relationship("RecItem", back_populates="priority")


# ── 5. Weekly Recommendation Summary ─────────────────────────────────────────

class RecWeekly(Base):
    """Aggregated weekly recommendation summary for one faculty member."""

    __tablename__ = "rec_weekly"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    faculty_id: Mapped[UUID] = mapped_column(
        ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False
    )
    week_label: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2026-W31"
    lecture_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Trends
    repeated_weaknesses: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    improving_areas: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    declining_areas: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    frequently_skipped_topics: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    frequently_incorrect_concepts: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Averages across lectures
    avg_coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_validation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_teaching_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")


# ── 6. Monthly Recommendation Summary ────────────────────────────────────────

class RecMonthly(Base):
    """Aggregated monthly recommendation summary for one faculty member."""

    __tablename__ = "rec_monthly"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    faculty_id: Mapped[UUID] = mapped_column(
        ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False
    )
    month_label: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "2026-08"
    week_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lecture_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Trends across weeks
    coverage_trend: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    validation_trend: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    teaching_trend: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    interaction_trend: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)

    overall_progress_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    monthly_improvement_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    top_recurring_issues: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    most_improved_areas: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")


# ── 7. Per-Lecture Summary ────────────────────────────────────────────────────

class RecSummary(Base):
    """High-level recommendation summary for a single lecture."""

    __tablename__ = "rec_summary"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(
        ForeignKey("rec_analyses.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    lecture_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False
    )

    total_recommendations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    informational_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    top_priority_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    overall_risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")
    analysis_reused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationship
    analysis: Mapped["RecAnalysis"] = relationship("RecAnalysis", back_populates="summary")
