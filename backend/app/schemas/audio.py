"""
Pydantic schemas for the Audio Intelligence & Speech Recognition API (Module 2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Diarized Transcript Segments ─────────────────────────────────────────────

class DiarizedSegmentItem(BaseModel):
    """Single diarized, timestamped speech segment."""
    segment_id: Optional[UUID] = None
    speaker: str = Field(default="Teacher", description="Identified speaker: 'Teacher' or 'Student'")
    start_time: float = Field(default=0.0, ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(default=0.0, ge=0.0, description="End timestamp in seconds")
    text: str = Field(default="", description="Spoken text in this segment")
    confidence: float = Field(default=0.92, ge=0.0, le=1.0, description="Speech recognition confidence")
    word_count: int = Field(default=0, ge=0)

    @property
    def start_sec(self) -> float:
        return self.start_time

    @property
    def end_sec(self) -> float:
        return self.end_time


# Alias for cross-module compatibility
TranscriptSegmentItem = DiarizedSegmentItem


class DiarizationSummary(BaseModel):
    """Aggregate speaker statistics for a lecture session."""
    total_segments: int = 0
    teacher_segments: int = 0
    student_segments: int = 0
    teacher_speaking_time_sec: float = 0.0
    student_speaking_time_sec: float = 0.0
    teacher_talk_ratio: float = Field(default=1.0, ge=0.0, le=1.0, description="Teacher talk time / Total talk time")
    total_words: int = 0


# ── VAD Speech Activity Segments ─────────────────────────────────────────────

class VADSegmentItem(BaseModel):
    """Active speech interval detected by Voice Activity Detection."""
    start_sec: float
    end_sec: float
    duration_sec: float
    energy_score: float = 1.0


# ── Audio Processing Requests & Responses ───────────────────────────────────

class AudioProcessRequest(BaseModel):
    """Options for processing lecture audio across diverse recording types."""
    model_size: Optional[str] = Field(default="base", description="Whisper model size: 'tiny', 'base', 'small'")
    language: Optional[str] = Field(default="auto", description="Audio language: 'auto' (detect automatically), 'en', 'hi', etc.")
    domain_subject: Optional[str] = Field(default="auto", description="Subject area: 'auto', 'cs', 'engineering', 'math', 'medical', 'business', 'general'")
    diarization_mode: Optional[str] = Field(default="lecture", description="Speaker mode: 'lecture' (Teacher/Student), 'discussion' (Multi-speaker), 'solo'")
    domain_vocabulary: Optional[List[str]] = Field(
        default=None,
        description="Custom technical terminology to inject into speech recognition (e.g. ['polymorphism', 'eigenvalue'])",
    )
    boost_audio_volume: bool = Field(default=True, description="Apply dynamic loudness normalization for quiet or phone-recorded audio")
    enable_vad: bool = Field(default=True, description="Enable Voice Activity Detection and silence trimming")
    enable_diarization: bool = Field(default=True, description="Enable speaker separation")
    sync_academic: bool = Field(default=True, description="Automatically feed transcript into Member 2's Academic Intelligence engine")


class AudioProcessResponse(BaseModel):
    """Response after executing the Audio Intelligence pipeline."""
    session_id: UUID
    transcript_id: UUID
    status: str = "COMPLETED"
    language: str = "en"
    total_words: int
    total_segments: int
    duration_seconds: float
    diarization_summary: DiarizationSummary
    segments: List[DiarizedSegmentItem] = Field(default_factory=list)
    academic_synced: bool = False
    academic_summary: Optional[Dict[str, Any]] = None
    processing_time_sec: float = 0.0


class AudioTranscriptResponse(BaseModel):
    """Full transcript retrieval response for a lecture session."""
    session_id: UUID
    transcript_id: Optional[UUID] = None
    has_transcript: bool
    language: str = "en"
    total_words: int = 0
    raw_text: Optional[str] = None
    diarization_summary: DiarizationSummary = Field(default_factory=DiarizationSummary)
    segments: List[DiarizedSegmentItem] = Field(default_factory=list)


class TranscriptSyncResponse(BaseModel):
    """Response after syncing transcript with Member 2's Academic Intelligence."""
    session_id: UUID
    transcript_id: UUID
    academic_status: str
    chunks_created: int
    mapped_chunks: int
    unmapped_chunks: int
    coverage_score: Optional[float] = None
    message: str
