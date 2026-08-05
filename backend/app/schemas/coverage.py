"""
Pydantic schemas for the Curriculum Coverage Intelligence Engine API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── Input Schemas ─────────────────────────────────────────────────────────────

class TranscriptChunkInput(BaseModel):
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
            raise ValueError("Transcript text cannot be empty")
        return v.strip()


class CoverageAnalyzeRequest(BaseModel):
    lecture_id: Optional[UUID] = None
    course_id: Optional[str] = None
    curriculum_id: Optional[UUID] = None
    faculty_id: Optional[UUID] = None
    chunks: List[TranscriptChunkInput] = Field(..., min_length=1)


# ── Response Schemas ──────────────────────────────────────────────────────────

class CoverageAnalyzeResponse(BaseModel):
    status: str = "SUCCESS"
    lecture_id: str
    covered_topics: int
    partially_covered: int
    skipped_topics: int
    rushed_topics: int
    over_explained: int
    repeated_topics: int
    weighted_coverage: float
    remaining_topics: int


class TopicCoverageResponseItem(BaseModel):
    id: str
    lecture_id: str
    curriculum_id: str
    topic_id: str
    topic_name: str
    coverage_status: str
    coverage_percentage: float
    expected_duration_seconds: float
    actual_duration_seconds: float
    duration_difference_seconds: float
    over_explained_percentage: float
    first_mentioned_time: Optional[float] = None
    last_mentioned_time: Optional[float] = None
    occurrence_count: int
    sequence_order_in_curriculum: int
    sequence_order_in_lecture: Optional[int] = None
    sequence_integrity_status: str


class RemainingCurriculumResponse(BaseModel):
    remaining_topics: List[Dict[str, Any]] = Field(default_factory=list)
    remaining_chapters: List[Dict[str, Any]] = Field(default_factory=list)
    remaining_units: List[Dict[str, Any]] = Field(default_factory=list)
    remaining_learning_outcomes: List[str] = Field(default_factory=list)


class TimelineIntervalItem(BaseModel):
    id: str
    topic_id: Optional[str] = None
    topic_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    status: str
    display_order: int


class CoverageTimelineResponse(BaseModel):
    status: str = "SUCCESS"
    lecture_id: str
    total_intervals: int
    intervals: List[TimelineIntervalItem] = Field(default_factory=list)


class CoverageSummaryResponse(BaseModel):
    lecture_id: str
    curriculum_id: str
    total_topics: int
    covered_topics: int
    partially_covered: int
    skipped_topics: int
    rushed_topics: int
    over_explained: int
    repeated_topics: int
    raw_coverage: float
    weighted_coverage: float
    remaining_topics: int
    sequence_score: float


class CoverageHistoryItem(BaseModel):
    """One entry in the coverage history list for a curriculum across lectures."""
    lecture_id: str
    curriculum_id: str
    total_topics: int
    covered_topics: int
    partially_covered: int
    skipped_topics: int
    weighted_coverage: float
    sequence_score: float
    created_at: str
