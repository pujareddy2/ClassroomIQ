"""
REST API router for Curriculum Coverage Intelligence Engine Module.

Routes:
  POST /coverage/analyze
  GET  /coverage/{lecture_id}
  GET  /coverage/{lecture_id}/topics
  GET  /coverage/{lecture_id}/remaining
  GET  /coverage/{lecture_id}/timeline
  GET  /coverage/{lecture_id}/summary
"""

from typing import List, Annotated
import logging
import time
from uuid import UUID
from app.schemas.response import ok, created, paginated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.coverage import (
    CoverageAnalyzeRequest,
    CoverageAnalyzeResponse,
    CoverageSummaryResponse,
    CoverageTimelineResponse,
    RemainingCurriculumResponse,
    TopicCoverageResponseItem,
)
from app.services.coverage.coverage_service import CoverageService
from app.services.coverage.exceptions import (
    CoverageError,
    CurriculumNotFoundError,
    EmptyTranscriptError,
    InvalidMetadataError,
    LectureNotFoundError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/coverage", tags=["Curriculum Coverage Intelligence Engine"])


@router.post(
    "/analyze",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
)
def analyze_curriculum_coverage(
    payload: CoverageAnalyzeRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    POST /coverage/analyze

    Receives structured transcript payload from Member 1.
    Analyzes covered, skipped, rushed, over-explained topics, teaching sequence integrity,
    weighted coverage %, remaining curriculum items, and persists to PostgreSQL.
    """
    start = time.time()
    service = CoverageService(db)
    try:
        chunk_items = [c.model_dump() for c in payload.chunks]
        result = service.analyze_lecture_coverage(
            transcript_chunks=chunk_items,
            lecture_id=payload.lecture_id,
            curriculum_id=payload.curriculum_id,
            course_id=payload.course_id,
            faculty_id=payload.faculty_id,
        )
        db.commit()
        return created(data=result, message="Coverage analysis completed.", start_ts=start)
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CurriculumNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidMetadataError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except CoverageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during curriculum coverage analysis")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/topics",
    response_model=List[TopicCoverageResponseItem],
    status_code=status.HTTP_200_OK,
)
def get_topic_coverage(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> List[TopicCoverageResponseItem]:
    """
    GET /coverage/{lecture_id}/topics

    Returns detailed topic-level coverage classifications, durations, and sequence integrity.
    """
    service = CoverageService(db)
    try:
        topics_data = service.get_topic_coverage(lecture_id)
        return [TopicCoverageResponseItem(**t) for t in topics_data]
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching topic coverage")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/remaining",
    response_model=RemainingCurriculumResponse,
    status_code=status.HTTP_200_OK,
)
def get_remaining_curriculum(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> RemainingCurriculumResponse:
    """
    GET /coverage/{lecture_id}/remaining

    Returns remaining un-covered topics, chapters, units, and learning outcomes for future planning.
    """
    service = CoverageService(db)
    try:
        remaining_data = service.get_remaining_curriculum(lecture_id)
        return RemainingCurriculumResponse(**remaining_data)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching remaining curriculum")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/timeline",
    response_model=CoverageTimelineResponse,
    status_code=status.HTTP_200_OK,
)
def get_coverage_timeline(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CoverageTimelineResponse:
    """
    GET /coverage/{lecture_id}/timeline

    Returns chronological timeline visualization intervals of covered topics for frontend UI.
    """
    service = CoverageService(db)
    try:
        timeline_data = service.get_coverage_timeline(lecture_id)
        return CoverageTimelineResponse(**timeline_data)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching coverage timeline")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/summary",
    response_model=CoverageSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_coverage_summary(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CoverageSummaryResponse:
    """
    GET /coverage/{lecture_id}/summary

    Returns aggregate lecture coverage summary statistics.
    """
    service = CoverageService(db)
    try:
        summary_data = service.get_coverage_summary(lecture_id)
        return CoverageSummaryResponse(**summary_data)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching coverage summary")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
