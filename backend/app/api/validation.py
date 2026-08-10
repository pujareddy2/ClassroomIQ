"""
REST API router for Technical Validation Engine Module.

Routes:
  POST /validation/analyze
  GET  /validation/{lecture_id}
  GET  /validation/{lecture_id}/summary
  GET  /validation/{lecture_id}/evidence
  GET  /validation/{lecture_id}/timeline
"""

from __future__ import annotations

import logging
import time
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.schemas.response import ok

from app.db.session import get_db
from app.schemas.validation import (
    EvidenceDetail,
    ValidationAnalyzeRequest,
    ValidationAnalyzeResponse,
    ValidationResultItem,
    ValidationSummaryResponse,
    ValidationTimelineResponse,
)
from app.services.validation.exceptions import (
    CurriculumNotFoundError,
    EmptyTranscriptError,
    LectureNotFoundError,
    ValidationError,
)
from app.services.validation.validation_service import ValidationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/validation", tags=["Technical Validation Engine"])


@router.post(
    "/analyze",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def analyze_lecture_transcript(
    payload: ValidationAnalyzeRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    POST /validation/analyze

    Receives structured transcript chunks (with topic_id) from Member 1 / Coverage Engine.
    Retrieves reference materials, detects correctness with modular validators,
    calculates quality scores, and persists results to PostgreSQL.
    """
    start = time.time()
    service = ValidationService(db)
    try:
        chunks = [c.model_dump() for c in payload.transcript_chunks]
        result = service.process_and_validate_transcript(
            transcript_chunks=chunks,
            lecture_id=payload.lecture_id,
            curriculum_id=payload.curriculum_id,
            course_id=payload.course_id,
            faculty_id=payload.faculty_id,
        )
        db.commit()
        return ok(data=result, message="Validation analysis completed.", start_ts=start)
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during lecture validation analysis")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_validation_results(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /validation/{lecture_id}

    Returns all detailed validation results and supporting evidence for a lecture.
    """
    service = ValidationService(db)
    try:
        results = service.get_validation_results(lecture_id)
        return ok(data=[ValidationResultItem(**r).model_dump() for r in results], message="Validation results retrieved.")
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching validation results")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/summary",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_validation_summary(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /validation/{lecture_id}/summary

    Returns aggregate validation summary counts, overall validation score, quality rating, and confidence distribution.
    """
    service = ValidationService(db)
    try:
        summary_data = service.get_validation_summary(lecture_id)
        return ok(data=summary_data, message="Validation summary retrieved.")
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching validation summary")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/evidence",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_validation_evidence(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /validation/{lecture_id}/evidence

    Returns supporting reference materials and evidence for a lecture's validation.
    """
    service = ValidationService(db)
    try:
        evidence_list = service.get_validation_evidence(lecture_id)
        return ok(data=[EvidenceDetail(**e).model_dump() for e in evidence_list], message="Validation evidence retrieved.")
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching validation evidence")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/timeline",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_validation_timeline(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /validation/{lecture_id}/timeline

    Returns chronological validation timeline intervals for UI video player visualization.
    Renders red/green bands across lecture playback timeline.
    """
    service = ValidationService(db)
    try:
        timeline_data = service.get_validation_timeline(lecture_id)
        return ok(data=timeline_data, message="Validation timeline retrieved.")
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching validation timeline")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
