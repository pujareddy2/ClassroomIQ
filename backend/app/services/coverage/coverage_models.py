"""
Internal pipeline models for Curriculum Coverage Intelligence Engine.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CoverageStatus(str, Enum):
    COVERED = "COVERED"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    SKIPPED = "SKIPPED"
    RUSHED = "RUSHED"
    OVER_EXPLAINED = "OVER_EXPLAINED"
    REPEATED = "REPEATED"
    NOT_SCHEDULED = "NOT_SCHEDULED"
    UNKNOWN = "UNKNOWN"


class SequenceStatus(str, Enum):
    CORRECT_SEQUENCE = "CORRECT_SEQUENCE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    SKIPPED_PREREQUISITE = "SKIPPED_PREREQUISITE"
    REPEATED_SEQUENCE = "REPEATED_SEQUENCE"


class TopicCoverageCalculation(BaseModel):
    topic_id: UUID
    topic_name: str
    sequence_order: int
    expected_duration_seconds: float
    actual_duration_seconds: float
    duration_difference_seconds: float
    over_explained_percentage: float
    coverage_percentage: float
    status: CoverageStatus
    occurrence_count: int
    first_mentioned_time: Optional[float] = None
    last_mentioned_time: Optional[float] = None
    sequence_order_in_lecture: Optional[int] = None
    sequence_integrity_status: SequenceStatus = SequenceStatus.CORRECT_SEQUENCE
    matching_chunks: List[dict] = Field(default_factory=list)
