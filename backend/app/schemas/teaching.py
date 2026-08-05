"""
Pydantic schemas for the Teaching Intelligence API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ────────────────────────────────────────────────────────────

class TranscriptChunkItem(BaseModel):
    chunk_id: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    speaker: str = "Faculty"
    text: str
    topic_id: Optional[str] = None


class TeachingAnalyzeRequest(BaseModel):
    """Payload to trigger pedagogical teaching analysis."""
    lecture_id: UUID
    curriculum_id: UUID
    coverage_summary_id: Optional[UUID] = None
    validation_summary_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None
    transcript_chunks: Optional[List[TranscriptChunkItem]] = None


# ── Response Schemas ──────────────────────────────────────────────────────────

class TeachingAnalyzeData(BaseModel):
    lecture_id: str
    teaching_score: float
    grade: str
    confidence: float
    explanation_score: float
    example_score: float
    structure_score: float
    interaction_score: float
    coverage_score: float
    validation_score: float
    strengths: List[str]
    weaknesses: List[str]
    analysis_reused: bool = False
    qualitative_summary: Optional[str] = None


class TeachingSummaryResponse(BaseModel):
    lecture_id: str
    teaching_score: float
    grade: str
    confidence: float
    qualitative_summary: Optional[str] = None


class TeachingStrengthsResponse(BaseModel):
    lecture_id: str
    strengths: List[str]


class TeachingWeaknessesResponse(BaseModel):
    lecture_id: str
    weaknesses: List[str]


class TeachingExampleItem(BaseModel):
    example_id: str
    example_type: str
    description: str
    relevance_score: float
    quality_score: float
    timestamp_start: float
    timestamp_end: float
    topic_id: Optional[str] = None


class TeachingExamplesResponse(BaseModel):
    lecture_id: str
    example_count: int
    examples: List[TeachingExampleItem]


class TeachingInteractionResponse(BaseModel):
    lecture_id: str
    interaction_score: float
    faculty_question_count: int
    student_question_count: int
    faculty_answer_count: int
    student_response_count: int
    interaction_density: float
    engagement_opportunities: int
    clarification_requests: int
    recap_questions: int


class TeachingStructureResponse(BaseModel):
    lecture_id: str
    structure_score: float
    has_introduction: bool
    has_conclusion: bool
    topic_jump_count: int
    improper_ordering_count: int
    missing_transitions_count: int
    continuity_score: float
    detected_flow: List[str]
