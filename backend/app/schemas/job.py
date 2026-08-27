"""
Pydantic schemas for the Async Media Processing Job API.
Used by both the audio and video background job endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobSubmitResponse(BaseModel):
    """Returned immediately (< 1s) when a background job is accepted."""

    job_id: UUID = Field(..., description="Poll this ID to track job progress")
    session_id: UUID
    job_type: str = Field(..., description="audio_process | video_process | full_pipeline")
    status: str = Field("PENDING", description="Always PENDING at submission time")
    message: str = Field(..., description="Human-readable confirmation")
    poll_url: str = Field(..., description="GET this URL to check job progress")


class JobStatusResponse(BaseModel):
    """Returned when polling GET /jobs/{job_id}."""

    job_id: UUID
    session_id: UUID
    job_type: str
    status: str = Field(..., description="PENDING | RUNNING | COMPLETED | FAILED")
    progress: int = Field(..., ge=0, le=100, description="0–100 progress percentage")
    result_summary: Optional[Dict[str, Any]] = Field(
        None, description="Partial result metadata once COMPLETED"
    )
    error_message: Optional[str] = Field(None, description="Set only if status=FAILED")
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SessionJobsResponse(BaseModel):
    """All jobs submitted for a given session."""

    session_id: UUID
    total: int
    jobs: List[JobStatusResponse]
