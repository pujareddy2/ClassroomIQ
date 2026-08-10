"""
Pydantic schemas for the Transcript Intelligence API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Input Schemas ─────────────────────────────────────────────────────────────

class TranscriptEntry(BaseModel):
    """Single diarized segment from Member 1's speech-to-text pipeline."""
    speaker: str = "Faculty"
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Transcript entry text cannot be empty")
        return v.strip()


class TranscriptUploadRequest(BaseModel):
    """Full transcript upload payload from Member 1."""
    lecture_id: Optional[UUID] = None
    course_id: Optional[str] = None        # course code or name
    faculty_name: Optional[str] = "Faculty"
    curriculum_id: Optional[UUID] = None
    transcript: List[TranscriptEntry] = Field(..., min_length=1)


# ── Response Schemas ──────────────────────────────────────────────────────────

class TranscriptUploadResponse(BaseModel):
    status: str = "SUCCESS"
    lecture_id: str
    transcript_id: str
    chunks: int
    mapped_chunks: int
    unmapped_chunks: int
    processing_time: str
    statistics: Dict[str, Any] = Field(default_factory=dict)


class ChunkResponse(BaseModel):
    chunk_id: str
    chunk_index: int
    start_time: float
    end_time: float
    speaker: str
    text: str
    sentence_count: int
    word_count: int


class MappingResponse(BaseModel):
    mapping_id: str
    chunk_id: str
    curriculum_id: str
    unit_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: str
    confidence_score: float
    mapping_reason: str


class LectureResponse(BaseModel):
    lecture_id: str
    course_id: str
    faculty_id: str
    lecture_date: str
    duration_minutes: int
    classroom: Optional[str] = None
    has_transcript: bool
    transcript_id: Optional[str] = None


class LectureStatisticsResponse(BaseModel):
    lecture_id: str
    total_sentences: int
    total_chunks: int
    mapped_chunks: int
    unmapped_chunks: int
    coverage_candidates: int
    average_chunk_length_words: float
    average_speaking_time_seconds: float


class LectureStatusResponse(BaseModel):
    """Processing status of a lecture session — for polling by Member 1 or Frontend."""
    lecture_id: str
    has_transcript: bool
    has_coverage: bool
    has_validation: bool
    processing_complete: bool
    status: str  # PENDING | TRANSCRIPT_READY | COVERAGE_READY | VALIDATION_READY | COMPLETE
