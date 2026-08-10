"""
ORM Models for the Explainable AI Engine.

Tables:
  explanation_records    — One explainability package per upstream AI decision
  evidence_items         — Each piece of supporting evidence (FK → upstream result rows)
  transcript_evidence    — Minimal transcript snippet supporting an evidence item
  reference_citations    — Verified academic citation supporting an evidence item
  confidence_breakdowns  — Deterministic 6-component confidence score breakdown
  reasoning_steps        — Ordered logical DAG reasoning steps per explanation
  explanation_summaries  — Lecture-level aggregate explainability stats

Design principles:
  - NEVER duplicate transcript/curriculum/coverage/validation/teaching/recommendation data.
  - All data is referenced via Foreign Keys to existing engine tables.
  - Only Explainability-specific columns are stored here.
  - One active explanation per (lecture_id, decision_source, decision_type, decision_id).
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Float, ForeignKey, Index, Integer,
    String, Text, TIMESTAMP, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── 1. Explanation Record ──────────────────────────────────────────────────────

class ExplanationRecord(Base):
    """
    One Explainability Package per upstream AI decision.

    decision_source:  'coverage' | 'validation' | 'teaching' | 'recommendation'
    decision_type:    e.g. 'SKIPPED_TOPIC', 'INCORRECT_CONCEPT', 'WEAK_EXPLANATION'
    decision_id:      UUID of the upstream record (CoverageResult.id, ValidationResult.id, etc.)
    status:           'ACTIVE' | 'SUPERSEDED' — only one ACTIVE per decision
    """

    __tablename__ = "explanation_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Context FKs — reference existing entities, never duplicate them
    lecture_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    faculty_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True, index=True
    )
    curriculum_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("curricula.id", ondelete="SET NULL"), nullable=True
    )

    # Decision identity — what upstream decision is being explained
    decision_source: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)
    decision_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)  # FK resolved at service layer

    # Output
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    explanation_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    # Relationships
    evidence_items: Mapped[List["EvidenceItem"]] = relationship(
        "EvidenceItem",
        back_populates="explanation_record",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    confidence_breakdown: Mapped[Optional["ConfidenceBreakdown"]] = relationship(
        "ConfidenceBreakdown",
        back_populates="explanation_record",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    reasoning_steps: Mapped[List["ReasoningStep"]] = relationship(
        "ReasoningStep",
        back_populates="explanation_record",
        cascade="all, delete-orphan",
        order_by="ReasoningStep.step_order",
        lazy="selectin",
    )

    # Composite unique: only one ACTIVE explanation per decision
    __table_args__ = (
        UniqueConstraint(
            "lecture_id", "decision_source", "decision_type", "decision_id", "status",
            name="uq_active_explanation_per_decision",
        ),
        Index("ix_explanation_lecture_source", "lecture_id", "decision_source"),
        Index("ix_explanation_status", "status"),
    )


# ── 2. Evidence Item ───────────────────────────────────────────────────────────

class EvidenceItem(Base):
    """
    One piece of supporting evidence for an ExplanationRecord.

    Directly references upstream result rows via nullable FKs.
    At most one of coverage_result_id / validation_result_id /
    teaching_analysis_id / recommendation_id is non-NULL per row.
    """

    __tablename__ = "evidence_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    explanation_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("explanation_records.id", ondelete="CASCADE"), nullable=False, index=True
    )

    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. 'coverage_result' | 'validation_result' | 'teaching_analysis' | 'recommendation'

    # Upstream result FKs — exactly one is populated per evidence row
    coverage_result_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("coverage_results.id", ondelete="SET NULL"), nullable=True, index=True
    )
    validation_result_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("validation_results.id", ondelete="SET NULL"), nullable=True, index=True
    )
    teaching_analysis_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("teaching_analysis.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recommendation_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("rec_items.id", ondelete="SET NULL"), nullable=True, index=True
    )

    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationships
    explanation_record: Mapped["ExplanationRecord"] = relationship(
        "ExplanationRecord", back_populates="evidence_items"
    )
    transcript_evidence: Mapped[Optional["TranscriptEvidence"]] = relationship(
        "TranscriptEvidence",
        back_populates="evidence_item",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    reference_citation: Mapped[Optional["ReferenceCitation"]] = relationship(
        "ReferenceCitation",
        back_populates="evidence_item",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    # Upstream result objects (loaded by service layer via joinedload when needed)
    coverage_result: Mapped[Optional["CoverageResult"]] = relationship(
        "CoverageResult",
        foreign_keys=[coverage_result_id],
        lazy="joined",
    )
    validation_result: Mapped[Optional["ValidationResult"]] = relationship(
        "ValidationResult",
        foreign_keys=[validation_result_id],
        lazy="joined",
    )
    teaching_analysis: Mapped[Optional["TeachingAnalysis"]] = relationship(
        "TeachingAnalysis",
        foreign_keys=[teaching_analysis_id],
        lazy="joined",
    )
    recommendation: Mapped[Optional["RecItem"]] = relationship(
        "RecItem",
        foreign_keys=[recommendation_id],
        lazy="joined",
    )


# ── 3. Transcript Evidence ─────────────────────────────────────────────────────

class TranscriptEvidence(Base):
    """
    Minimal transcript snippet (≤ 300 chars) supporting a single evidence item.
    References the lecture session for context.
    Never stores the full transcript — only the minimal passage.
    """

    __tablename__ = "transcript_evidence"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evidence_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    lecture_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Identifying the source chunk (chunk_id is the string key used by TranscriptChunk)
    chunk_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    speaker: Mapped[str] = mapped_column(String(100), nullable=False, default="Faculty")
    snippet: Mapped[str] = mapped_column(Text, nullable=False)   # max 300 chars, enforced in service
    start_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationships
    evidence_item: Mapped["EvidenceItem"] = relationship(
        "EvidenceItem", back_populates="transcript_evidence"
    )


# ── 4. Reference Citation ──────────────────────────────────────────────────────

class ReferenceCitation(Base):
    """
    Verified academic citation tied to a single evidence item.
    reference_material_id FK ensures we only cite uploaded, verified documents.
    Falls back to document_name = 'Reference Not Available' when no match.
    """

    __tablename__ = "reference_citations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evidence_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # FK to the actual uploaded reference document — NULL means no match found
    reference_material_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("reference_materials.id", ondelete="SET NULL"), nullable=True, index=True
    )

    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, default="TEXTBOOK")
    chapter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationships
    evidence_item: Mapped["EvidenceItem"] = relationship(
        "EvidenceItem", back_populates="reference_citation"
    )
    reference_material: Mapped[Optional["ReferenceMaterial"]] = relationship(
        "ReferenceMaterial",
        foreign_keys=[reference_material_id],
        lazy="joined",
    )


# ── 5. Confidence Breakdown ────────────────────────────────────────────────────

class ConfidenceBreakdown(Base):
    """
    Deterministic confidence breakdown per ExplanationRecord.

    Six sub-scores feed a weighted formula:
      overall = 0.25*topic_match + 0.20*coverage + 0.20*validation
              + 0.15*reference + 0.10*teaching + 0.10*recommendation
    """

    __tablename__ = "confidence_breakdowns"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    explanation_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("explanation_records.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    topic_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    validation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reference_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    teaching_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationship
    explanation_record: Mapped["ExplanationRecord"] = relationship(
        "ExplanationRecord", back_populates="confidence_breakdown"
    )


# ── 6. Reasoning Step ─────────────────────────────────────────────────────────

class ReasoningStep(Base):
    """
    One logical reasoning step in the ordered DAG for an ExplanationRecord.
    Follows: Observation (1) → Evidence (2) → Analysis (3) → Conclusion (4).
    """

    __tablename__ = "reasoning_steps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    explanation_record_id: Mapped[UUID] = mapped_column(
        ForeignKey("explanation_records.id", ondelete="CASCADE"), nullable=False, index=True
    )

    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)

    # Relationship
    explanation_record: Mapped["ExplanationRecord"] = relationship(
        "ExplanationRecord", back_populates="reasoning_steps"
    )

    # Unique: one step_order per explanation
    __table_args__ = (
        UniqueConstraint("explanation_record_id", "step_order", name="uq_reasoning_step_order"),
        Index("ix_reasoning_record_order", "explanation_record_id", "step_order"),
    )


# ── 7. Explanation Summary ─────────────────────────────────────────────────────

class ExplanationSummary(Base):
    """
    Lecture-level aggregate explainability statistics.
    One record per lecture (upserted after all explanations are built).
    """

    __tablename__ = "explanation_summaries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(
        ForeignKey("lecture_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    total_explanations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    highest_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lowest_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    processing_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
