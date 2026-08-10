"""
Pydantic schemas for the Technical Validation Engine API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Input Schemas ─────────────────────────────────────────────────────────────

class Member1TranscriptChunk(BaseModel):
    """Structured transcript chunk payload received from Member 1 / Coverage Engine."""
    chunk_id: str
    topic_id: Optional[UUID] = None
    speaker: str = "Faculty"
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Transcript chunk text cannot be empty")
        return v.strip()


class ValidationAnalyzeRequest(BaseModel):
    """Full input payload for technical validation analysis."""
    lecture_id: Optional[UUID] = None
    curriculum_id: Optional[UUID] = None
    course_id: Optional[str] = None
    faculty_id: Optional[UUID] = None
    transcript_chunks: List[Member1TranscriptChunk] = Field(..., min_length=1)


# ── Response Schemas ──────────────────────────────────────────────────────────

class ValidationAnalyzeResponse(BaseModel):
    status: str = "SUCCESS"
    lecture_id: str
    validated_chunks: int
    correct_concepts: int
    incorrect_concepts: int
    formula_issues: int
    code_issues: int
    missing_concepts: int = 0
    terminology_errors: int = 0
    overall_validation_score: float = 100.0
    lecture_quality: str = "EXCELLENT"
    validation_percentage: float = 100.0
    average_confidence: float


class EvidenceDetail(BaseModel):
    id: str
    validation_result_id: str
    reference_document: str
    reference_section: Optional[str] = None
    reference_excerpt: str
    curriculum_topic: str
    explanation: str


class ValidationResultItem(BaseModel):
    id: str
    lecture_id: str
    curriculum_id: str
    topic_id: Optional[str] = None
    chunk_id: str
    chunk_text: str
    chunk_start_time: float
    chunk_end_time: float
    speaker: str
    category: str = "CONCEPT"
    validation_status: str = "CORRECT"
    validation_type: str = "CORRECT"
    severity: str
    confidence_score: float
    confidence_level: str
    reason: str
    evidence: List[EvidenceDetail] = Field(default_factory=list)


class ValidationSummaryResponse(BaseModel):
    lecture_id: str
    curriculum_id: str
    validated_chunks: int
    correct_concepts: int
    incorrect_concepts: int
    formula_issues: int
    code_issues: int
    missing_concepts: int
    terminology_errors: int
    overall_validation_score: float
    lecture_quality: str
    validation_percentage: float
    average_confidence: float
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)


# ── NEW: Timeline Visualization Schema ───────────────────────────────────────

class TimelineInterval(BaseModel):
    chunk_id: str
    start_time: float
    end_time: float
    speaker: str
    category: str
    status: str
    severity: str
    confidence_score: float
    text_snippet: str
    reason: str


class ValidationTimelineResponse(BaseModel):
    status: str = "SUCCESS"
    lecture_id: str
    total_duration_seconds: float
    intervals: List[TimelineInterval] = Field(default_factory=list)


class ValidationIssueItem(BaseModel):
    """High-severity validation issue — INCORRECT, FORMULA_ERROR, or CODE_ERROR."""
    id: str
    chunk_id: str
    chunk_text: str
    chunk_start_time: float
    chunk_end_time: float
    category: str
    validation_status: str
    severity: str
    confidence_score: float
    reason: str
    evidence: List[EvidenceDetail] = Field(default_factory=list)
