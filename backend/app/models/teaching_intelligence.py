from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Integer, Float, ForeignKey, TIMESTAMP, String, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


def _now():
    return datetime.now(timezone.utc)


class TeachingScoreWeight(Base):
    __tablename__ = "teaching_score_weights"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)  # e.g., 30.0 for 30%
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


class TeachingAnalysis(Base):
    __tablename__ = "teaching_analysis"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)
    curriculum_id: Mapped[UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False)
    coverage_summary_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("coverage_summaries.id", ondelete="SET NULL"), nullable=True)
    validation_summary_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("validation_summaries.id", ondelete="SET NULL"), nullable=True)
    faculty_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)

    prerequisite_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    regeneration_trigger: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


class TeachingSummary(Base):
    __tablename__ = "teaching_summary"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("teaching_analysis.id", ondelete="CASCADE"), nullable=False, unique=True)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)

    overall_teaching_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    teaching_grade: Mapped[str] = mapped_column(String(5), nullable=False, default="C")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)

    explanation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    example_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    structure_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    interaction_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    validation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    strengths: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    qualitative_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analysis_reused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


class TeachingExplanation(Base):
    __tablename__ = "teaching_explanation"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("teaching_analysis.id", ondelete="CASCADE"), nullable=False, unique=True)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    definition_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    concept_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    logical_progression: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    step_by_step_clarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    coherence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    redundancy_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    strengths: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


class TeachingExample(Base):
    __tablename__ = "teaching_examples"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("teaching_analysis.id", ondelete="CASCADE"), nullable=False)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)

    example_type: Mapped[str] = mapped_column(String(50), nullable=False, default="General")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timestamp_start: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timestamp_end: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


class TeachingStructure(Base):
    __tablename__ = "teaching_structure"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("teaching_analysis.id", ondelete="CASCADE"), nullable=False, unique=True)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    has_introduction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_conclusion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    topic_jump_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    improper_ordering_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_transitions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    continuity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    detected_flow: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)


class TeachingInteraction(Base):
    __tablename__ = "teaching_interaction"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("teaching_analysis.id", ondelete="CASCADE"), nullable=False, unique=True)
    lecture_id: Mapped[UUID] = mapped_column(ForeignKey("lecture_sessions.id", ondelete="CASCADE"), nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    faculty_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    student_question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    faculty_answer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    student_response_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interaction_density: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    engagement_opportunities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clarification_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recap_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=_now)
