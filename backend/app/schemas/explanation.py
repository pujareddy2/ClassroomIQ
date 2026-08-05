"""
Pydantic Schemas for the Explainable AI Engine.

Used for validation of service inputs/outputs and future API layer.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Evidence Schemas ──────────────────────────────────────────────────────────

class EvidenceItemSchema(BaseModel):
    id: str
    evidence_type: str
    coverage_result_id: Optional[str] = None
    validation_result_id: Optional[str] = None
    teaching_analysis_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    importance_score: float
    transcript_snippet: Optional["TranscriptEvidenceSchema"] = None
    reference_citation: Optional["ReferenceCitationSchema"] = None


class TranscriptEvidenceSchema(BaseModel):
    chunk_id: Optional[str] = None
    speaker: str = "Faculty"
    snippet: str
    start_time: float
    end_time: float


class ReferenceCitationSchema(BaseModel):
    reference_material_id: Optional[str] = None
    document_name: str
    document_type: str = "TEXTBOOK"
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: Optional[int] = None
    excerpt: Optional[str] = None
    citation_confidence: float = 0.0


# ── Confidence Schemas ────────────────────────────────────────────────────────

class ConfidenceBreakdownSchema(BaseModel):
    topic_match_score: float
    coverage_score: float
    validation_score: float
    reference_score: float
    teaching_score: float
    recommendation_score: float
    overall_confidence: float


# ── Reasoning Schemas ─────────────────────────────────────────────────────────

class ReasoningStepSchema(BaseModel):
    step_order: int
    reason: str
    evidence_reference: Optional[str] = None


# ── Explanation Record Schemas ────────────────────────────────────────────────

class ExplanationRecordSchema(BaseModel):
    id: str
    lecture_id: str
    faculty_id: Optional[str] = None
    curriculum_id: Optional[str] = None
    decision_source: str
    decision_type: str
    decision_id: Optional[str] = None
    overall_confidence: float
    explanation_summary: str
    status: str
    evidence_items: List[EvidenceItemSchema] = Field(default_factory=list)
    confidence_breakdown: Optional[ConfidenceBreakdownSchema] = None
    reasoning_steps: List[ReasoningStepSchema] = Field(default_factory=list)


# ── Summary Schemas ───────────────────────────────────────────────────────────

class ExplanationSummarySchema(BaseModel):
    lecture_id: str
    total_explanations: int
    average_confidence: float
    highest_confidence: float
    lowest_confidence: float
    processing_time: float


# ── Request Schemas (for future API layer) ────────────────────────────────────

class ExplainRequest(BaseModel):
    lecture_id: UUID
    faculty_id: Optional[UUID] = None
    curriculum_id: Optional[UUID] = None
    force_rebuild: bool = False


class ExplainGenerateRequest(BaseModel):
    lecture_id: UUID = Field(..., description="Lecture session identifier to explain")
    faculty_id: Optional[UUID] = Field(None, description="Faculty identifier for ownership context")
    curriculum_id: Optional[UUID] = Field(None, description="Curriculum identifier used for reference matching")


class TranscriptSnippetResponseSchema(BaseModel):
    chunk_id: Optional[str] = None
    speaker: str = "Faculty"
    snippet: str
    start_time: float
    end_time: float
    topic: Optional[str] = None


class CitationResponseSchema(BaseModel):
    book: Optional[str] = None
    notes: Optional[str] = None
    reference_material: Optional[str] = None
    curriculum: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    excerpt: Optional[str] = None


class ConfidenceSummaryResponseSchema(BaseModel):
    topic_match: float = 0.0
    coverage: float = 0.0
    validation: float = 0.0
    reference: float = 0.0
    teaching: float = 0.0
    recommendation: float = 0.0
    overall: float = 0.0


class DecisionResponseSchema(BaseModel):
    decision_id: Optional[str] = None
    decision_type: Optional[str] = None
    decision_source: Optional[str] = None
    reason: Optional[str] = None
    transcript: Optional[TranscriptSnippetResponseSchema] = None
    citation: Optional[CitationResponseSchema] = None
    confidence: Optional[ConfidenceSummaryResponseSchema] = None
    reasoning: List[ReasoningStepSchema] = Field(default_factory=list)


class ExplanationPackageResponseSchema(BaseModel):
    lecture_id: str
    overall_confidence: float = 0.0
    decision_count: int = 0
    summary: Optional["ExplanationSummarySchema"] = None
    decisions: List[DecisionResponseSchema] = Field(default_factory=list)


class ExplanationSummaryResponseSchema(BaseModel):
    lecture_id: str
    total_explanations: int = 0
    average_confidence: float = 0.0
    highest_confidence: float = 0.0
    lowest_confidence: float = 0.0
    processing_time: float = 0.0
    decision_counts: dict[str, int] = Field(default_factory=dict)


class EvidenceCollectionResponseSchema(BaseModel):
    explanation_id: Optional[str] = None
    decision_id: Optional[str] = None
    decision_type: Optional[str] = None
    evidence_type: Optional[str] = None
    importance_score: float = 0.0
    transcript: Optional[TranscriptSnippetResponseSchema] = None
    citation: Optional[CitationResponseSchema] = None
    coverage_result_id: Optional[str] = None
    validation_result_id: Optional[str] = None
    teaching_analysis_id: Optional[str] = None
    recommendation_id: Optional[str] = None


class ReasoningCollectionResponseSchema(BaseModel):
    decision_id: Optional[str] = None
    decision_type: Optional[str] = None
    step_order: int = 0
    reason: str = ""
    evidence_reference: Optional[str] = None


class TimelineEntryResponseSchema(BaseModel):
    decision_id: Optional[str] = None
    decision_type: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    speaker: Optional[str] = None
    snippet: Optional[str] = None
    topic: Optional[str] = None


# Fix forward references
EvidenceItemSchema.model_rebuild()
