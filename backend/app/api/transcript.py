"""
REST API router for Transcript Intelligence Module.

Routes:
  POST /lecture/upload-transcript
  GET  /lecture/{lecture_id}
  GET  /lecture/{lecture_id}/chunks
  GET  /lecture/{lecture_id}/mappings
  GET  /lecture/{lecture_id}/statistics
"""

from __future__ import annotations

import logging
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.transcript import (
    ChunkResponse,
    LectureResponse,
    LectureStatisticsResponse,
    MappingResponse,
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
router = APIRouter(prefix="/lecture", tags=["Transcript Intelligence"])


@router.post(
    "/upload-transcript",
    response_model=TranscriptUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_transcript(
    payload: TranscriptUploadRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TranscriptUploadResponse:
    """
    POST /lecture/upload-transcript

    Receives a structured transcript from Member 1's Multimedia Intelligence pipeline.
    Performs cleaning → segmentation → semantic chunking → curriculum mapping →
    DB persistence → statistics. Returns summary and statistics.
    """
    service = TranscriptService(db)
    try:
        transcript_items = [t.model_dump() for t in payload.transcript]
        result = service.process_and_store_transcript(
            lecture_id=payload.lecture_id,
            course_name_or_code=payload.course_id or "Unknown Course",
            faculty_name=payload.faculty_name or "Faculty",
            transcript_data=transcript_items,
            curriculum_id=payload.curriculum_id,
        )
        db.commit()
        return TranscriptUploadResponse(**result)

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
    response_model=LectureResponse,
    status_code=status.HTTP_200_OK,
)
def get_lecture(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> LectureResponse:
    """
    GET /lecture/{lecture_id}

    Returns lecture session metadata and transcript linkage.
    """
    service = TranscriptService(db)
    try:
        data = service.get_lecture(lecture_id)
        return LectureResponse(**data)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching lecture")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/chunks",
    response_model=List[ChunkResponse],
    status_code=status.HTTP_200_OK,
)
def get_lecture_chunks(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> List[ChunkResponse]:
    """
    GET /lecture/{lecture_id}/chunks

    Returns all semantic transcript chunks for a given lecture.
    """
    service = TranscriptService(db)
    try:
        chunks = service.get_lecture_chunks(lecture_id)
        return [ChunkResponse(**c) for c in chunks]
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching chunks")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/mappings",
    response_model=List[MappingResponse],
    status_code=status.HTTP_200_OK,
)
def get_lecture_mappings(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> List[MappingResponse]:
    """
    GET /lecture/{lecture_id}/mappings

    Returns all transcript-to-curriculum-topic mappings for a lecture.
    """
    service = TranscriptService(db)
    try:
        mappings = service.get_lecture_mappings(lecture_id)
        return [MappingResponse(**m) for m in mappings]
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching mappings")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/statistics",
    response_model=LectureStatisticsResponse,
    status_code=status.HTTP_200_OK,
)
def get_lecture_statistics(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> LectureStatisticsResponse:
    """
    GET /lecture/{lecture_id}/statistics

    Returns aggregate statistics for transcript processing and curriculum mapping.
    """
    service = TranscriptService(db)
    try:
        stats = service.get_lecture_statistics(lecture_id)
        return LectureStatisticsResponse(**stats)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
