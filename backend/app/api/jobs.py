"""
REST API Router for Async Media Processing Job Status.
Prefix: /api/v1/jobs
"""

from __future__ import annotations

import logging
import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobStatusResponse, SessionJobsResponse
from app.schemas.response import ok
from app.services.job_service import MediaJobService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Async Media Processing Jobs"])


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Poll async job status",
    description=(
        "Poll this endpoint after submitting an audio or video processing job. "
        "Returns PENDING → RUNNING (with 0–100 progress) → COMPLETED | FAILED. "
        "Recommended polling interval: every 3–5 seconds."
    ),
)
def get_job_status(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    svc = MediaJobService(db)
    job = svc.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )
    return ok(data=svc.to_status_response(job).model_dump(mode="json"), message="Job status retrieved.", start_ts=start_ts)


@router.get(
    "/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="List all processing jobs for a session",
    description="Returns all audio/video jobs submitted for a given lecture session, ordered newest first.",
)
def list_session_jobs(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    svc = MediaJobService(db)
    jobs = svc.get_session_jobs(session_id)
    job_responses = [svc.to_status_response(j).model_dump(mode="json") for j in jobs]
    payload = SessionJobsResponse(
        session_id=session_id,
        total=len(job_responses),
        jobs=job_responses,
    )
    return ok(data=payload.model_dump(mode="json"), message="Session jobs retrieved.", start_ts=start_ts)
