"""
Pydantic schemas for Lecture Structuring, Media Synchronization & Member Handover Contract (Module 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.audio import TranscriptSegmentItem
from app.schemas.video import SceneType, VisualTimelineEvent


class SyncPoint(BaseModel):
    """Represents a unified synchronization checkpoint across Audio, Video, and Slides."""

    timestamp_sec: float = Field(..., description="Timestamp in seconds from lecture start")
    speech_text: Optional[str] = Field(default=None, description="Spoken words at this timestamp")
    speaker: Optional[str] = Field(default="Teacher", description="Speaker identity (Teacher / Student)")
    visual_scene: SceneType = Field(default=SceneType.TEACHER_LECTURING, description="Active visual scene modality")
    slide_number: Optional[int] = Field(default=None, description="Active slide number if presentation was shown")
    slide_title: Optional[str] = Field(default=None, description="Title of active slide")
    keyframe_url: Optional[str] = Field(default=None, description="Keyframe image snapshot filename")


class TopicSegmentItem(BaseModel):
    """Represents a structured semantic chapter / topic segment within the lecture."""

    segment_id: str = Field(..., description="Unique chapter identifier")
    title: str = Field(..., description="Topic chapter title")
    summary: str = Field(..., description="Concise synopsis of concepts explained in this section")
    start_time_sec: float = Field(..., ge=0.0)
    end_time_sec: float = Field(..., ge=0.0)
    duration_sec: float = Field(..., ge=0.0)
    key_concepts: List[str] = Field(default_factory=list, description="Extracted terminology and key keywords")
    primary_speaker: str = Field(default="Teacher")
    dominant_modality: str = Field(default="TEACHER_LECTURING", description="Primary visual teaching mode")
    utterance_count: int = Field(default=1)
    slide_numbers: List[int] = Field(default_factory=list, description="Referenced presentation slide indices")


class LectureStructuringMetadata(BaseModel):
    """Aggregate multi-modal analytics and speaking dynamics for the lecture."""

    total_duration_sec: float
    total_words: int
    words_per_minute: float
    pace_rating: str = Field(..., description="Speaking pace rating: OPTIMAL, RUSHED, SLOW")
    teacher_talk_ratio: float = Field(..., ge=0.0, le=1.0)
    student_talk_ratio: float = Field(..., ge=0.0, le=1.0)
    board_writing_ratio: float = Field(..., ge=0.0, le=1.0)
    slide_presentation_ratio: float = Field(..., ge=0.0, le=1.0)
    total_topic_segments: int
    extracted_keywords: List[str] = Field(default_factory=list)
    sync_quality_score: float = Field(default=0.95, ge=0.0, le=1.0)


class StructuredLectureResponse(BaseModel):
    """
    The definitive Member 1 -> Member 2 Handover Contract.
    Contains clean transcripts, speaker labels, visual event timelines, media sync points,
    and structured topic segments ready for Academic Reasoning and RAG.
    """

    session_id: UUID
    course_name: str
    faculty_name: str
    lecture_date: str
    status: str = "STRUCTURED"
    metadata: LectureStructuringMetadata
    topic_segments: List[TopicSegmentItem]
    synchronized_timeline: List[SyncPoint]
    transcript_segments: List[TranscriptSegmentItem]
    visual_events: List[VisualTimelineEvent]
    slides_count: int = 0
    structured_at: str


class LectureStructureProcessRequest(BaseModel):
    min_topic_duration_sec: float = Field(default=15.0, ge=5.0, description="Minimum duration for a distinct topic segment")
    sync_resolution_sec: float = Field(default=2.0, ge=0.5, le=10.0, description="Sampling resolution for multi-track sync points")
    auto_persist_db: bool = Field(default=True, description="Persist transcript segments to PostgreSQL database")
