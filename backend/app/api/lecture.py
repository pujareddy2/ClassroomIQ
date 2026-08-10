"""
REST API router for Lecture Intelligence Module.
Versioned under /api/v1/lecture (prefix applied at registration in main.py).

Public Routes (consumed by Frontend & Member 1):
  POST /lecture/analyze        — Member 1 submits structured transcript JSON
  GET  /lecture/{id}           — Lecture session metadata
  GET  /lecture/{id}/status    — Processing pipeline status
  GET  /lecture/{id}/statistics — Transcript aggregate statistics

Internal routes (removed from public API):
  - GET /lecture/{id}/chunks   — internal implementation detail
  - GET /lecture/{id}/mappings — internal implementation detail
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response import ok, created
from app.schemas.transcript import (
    LectureResponse,
    LectureStatisticsResponse,
    LectureStatusResponse,
    TranscriptUploadRequest,
    TranscriptUploadResponse,
)
from app.services.transcript.exceptions import (
    EmptyTranscriptError,
    LectureNotFoundError,
    TranscriptValidationError,
)
from app.services.transcript.transcript_service import TranscriptService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lecture", tags=["Lecture Intelligence"])


@router.post(
    "/analyze",
    status_code=status.HTTP_201_CREATED,
    summary="Submit structured transcript from Member 1",
    description=(
        "Receives a structured transcript payload produced by Member 1's Multimedia Intelligence pipeline. "
        "Performs cleaning → sentence segmentation → semantic chunking → curriculum topic mapping → "
        "PostgreSQL persistence → statistics generation. Returns a summary with chunk counts and mapping coverage."
    ),
)
def analyze_transcript(
    payload: TranscriptUploadRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    POST /api/v1/lecture/analyze

    Member 1 endpoint — accepts structured diarized transcript JSON.
    Previously named: POST /lecture/upload-transcript
    """
    service = TranscriptService(db)
    try:
        import time
        start = time.time()
        transcript_items = [t.model_dump() for t in payload.transcript]
        result = service.process_and_store_transcript(
            lecture_id=payload.lecture_id,
            course_name_or_code=payload.course_id or "Unknown Course",
            faculty_name=payload.faculty_name or "Faculty",
            transcript_data=transcript_items,
            curriculum_id=payload.curriculum_id,
        )
        db.commit()
        return created(
            data=TranscriptUploadResponse(**result).model_dump(),
            message="Transcript processed and stored successfully.",
            start_ts=start,
        )
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TranscriptValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error processing transcript")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}",
    status_code=status.HTTP_200_OK,
    summary="Get lecture session metadata",
    description="Returns lecture session metadata including course, faculty, date, duration, and transcript linkage.",
)
def get_lecture(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        import time
        start = time.time()
        data = service.get_lecture(lecture_id)
        return ok(
            data=LectureResponse(**data).model_dump(),
            message="Lecture metadata retrieved.",
            start_ts=start,
        )
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching lecture")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Get lecture processing pipeline status",
    description=(
        "Returns whether transcript, coverage, and validation processing has completed for a lecture. "
        "Used by Member 1 and Frontend to poll processing state."
    ),
)
def get_lecture_status(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        import time
        start = time.time()
        data = service.get_lecture_status(lecture_id)
        return ok(
            data=LectureStatusResponse(**data).model_dump(),
            message="Lecture processing status retrieved.",
            start_ts=start,
        )
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching lecture status")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/statistics",
    status_code=status.HTTP_200_OK,
    summary="Get lecture transcript processing statistics",
    description="Returns aggregate statistics for transcript processing: chunk counts, mapping coverage, speaking time.",
)
def get_lecture_statistics(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        import time
        start = time.time()
        stats = service.get_lecture_statistics(lecture_id)
        return ok(
            data=LectureStatisticsResponse(**stats).model_dump(),
            message="Lecture statistics retrieved.",
            start_ts=start,
        )
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
