"""
Pydantic schemas for the Multimedia Capture & Lecture Ingestion API (Module 1).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Live Recording Session Schemas ──────────────────────────────────────────

class SessionInitRequest(BaseModel):
    """Payload to start a live lecture recording session."""
    course_name_or_code: str = Field(default="General Lecture", description="Course code or name")
    faculty_name: Optional[str] = Field(default="Faculty", description="Name of the instructor")
    title: Optional[str] = Field(default="Classroom Lecture", description="Lecture topic or title")
    classroom: Optional[str] = Field(default=None, description="Classroom room number or identifier")
    consent_confirmed: bool = Field(default=True, description="Explicit faculty/classroom recording consent")
    has_screen_share: bool = Field(default=False, description="Whether screen/smart-board capture is active")


class SessionInitResponse(BaseModel):
    """Response returned when a recording session is initialized."""
    session_id: UUID
    recording_id: UUID
    status: str
    started_at: datetime
    upload_chunk_url: str
    complete_session_url: str


class ChunkUploadResponse(BaseModel):
    """Response after ingesting a live stream chunk."""
    session_id: UUID
    chunk_index: int
    bytes_written: int
    total_chunks: int
    status: str = "CHUNK_RECEIVED"


class SessionCompleteRequest(BaseModel):
    """Payload to finalize a live recording session."""
    duration_seconds: Optional[float] = Field(default=None, ge=0.0)
    course_name_or_code: Optional[str] = None
    faculty_name: Optional[str] = None
    title: Optional[str] = None
    classroom: Optional[str] = None
    notes: Optional[str] = None


class SessionCompleteResponse(BaseModel):
    """Response after completing and processing a recording session."""
    session_id: UUID
    recording_id: UUID
    status: str
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    audio_16k_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    slide_count: int = 0
    message: str = "Session completed and queued for AI intelligence pipeline."


# ── Batch Upload Schemas ───────────────────────────────────────────────────

class LectureUploadResponse(BaseModel):
    """Response returned after uploading a full lecture recording and optional slides."""
    session_id: UUID
    recording_id: UUID
    title: str
    course_name: str
    faculty_name: str
    video_filename: Optional[str] = None
    audio_filename: Optional[str] = None
    slides_filename: Optional[str] = None
    has_extracted_audio: bool = False
    slide_count: int = 0
    status: str
    created_at: datetime


# ── Media & Slide Metadata Schemas ──────────────────────────────────────────

class MediaMetadataResponse(BaseModel):
    """Technical metadata for a media file."""
    format: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: int = 0
    has_video: bool = False
    has_audio: bool = False
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class SlideItemResponse(BaseModel):
    """Details for a single extracted slide / smart-board frame."""
    slide_number: int
    title: Optional[str] = None
    text_content: str = ""
    preview_url: Optional[str] = None


class SlideSummaryResponse(BaseModel):
    """Summary of slides extracted for a lecture session."""
    session_id: UUID
    total_slides: int
    slides: List[SlideItemResponse] = Field(default_factory=list)


# ── Session Query Schemas ──────────────────────────────────────────────────

class SessionSummaryResponse(BaseModel):
    """High-level summary of a lecture recording session."""
    session_id: UUID
    recording_id: Optional[UUID] = None
    title: Optional[str] = None
    course_name: Optional[str] = None
    faculty_name: Optional[str] = None
    classroom: Optional[str] = None
    status: str
    created_at: datetime
    duration_seconds: Optional[float] = None
    has_video: bool = False
    has_audio: bool = False
    has_slides: bool = False
    slide_count: int = 0


class SessionDetailResponse(BaseModel):
    """Complete detail of a lecture session with media paths and pipeline flags."""
    session_id: UUID
    recording_id: Optional[UUID] = None
    title: Optional[str] = None
    course_name: Optional[str] = None
    faculty_name: Optional[str] = None
    classroom: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    duration_seconds: Optional[float] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    audio_16k_url: Optional[str] = None
    slides_url: Optional[str] = None
    slide_count: int = 0
    slides: List[SlideItemResponse] = Field(default_factory=list)
    media_metadata: Optional[MediaMetadataResponse] = None
    has_transcript: bool = False
    has_coverage: bool = False
    has_validation: bool = False


class SessionListResponse(BaseModel):
    """List response for lecture sessions."""
    total: int
    items: List[SessionSummaryResponse]
