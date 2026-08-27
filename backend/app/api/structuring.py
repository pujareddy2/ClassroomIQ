"""
REST API Router for Lecture Structuring & Multi-Track Media Synchronization (Module 4).
Exposes the Member 1 -> Member 2 Structured Lecture Handover Contract.
"""

from __future__ import annotations

import logging
from typing import Annotated, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.structuring import (
    LectureStructureProcessRequest,
    StructuredLectureResponse,
    SyncPoint,
    TopicSegmentItem,
)
from app.services.multimedia.storage_service import MultimediaStorageService
from app.services.structuring.lecture_structuring_service import LectureStructuringService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/structuring", tags=["Lecture Structuring"])

storage_service = MultimediaStorageService()
_STRUCTURED_LECTURE_CACHE: Dict[str, StructuredLectureResponse] = {}


@router.post(
    "/process/{session_id}",
    response_model=StructuredLectureResponse,
    status_code=status.HTTP_200_OK,
    summary="Process & Structure Lecture (Member 1 -> Member 2 Handover)",
)
def process_structured_lecture(
    session_id: UUID,
    request: Optional[LectureStructureProcessRequest] = None,
    db: Session = Depends(get_db),
) -> StructuredLectureResponse:
    """
    Synthesizes Audio Intelligence (transcripts & speaker diarization),
    Video Intelligence (OpenCV scenes & visual events), and Slide Decks into
    a unified, synchronized, structured lecture asset.
    """
    structuring_service = LectureStructuringService(db=db, storage_service=storage_service)
    try:
        response = structuring_service.process_and_structure_lecture(
            session_id=session_id,
            request=request,
            db=db,
        )
        _STRUCTURED_LECTURE_CACHE[str(session_id)] = response
        return response
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.exception("Lecture structuring failed for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lecture Structuring pipeline failed: {str(exc)}",
        )


@router.get(
    "/structured-lecture/{session_id}",
    response_model=StructuredLectureResponse,
    summary="Get Complete Member 1 Handover Contract",
)
def get_structured_lecture(
    session_id: UUID,
    db: Session = Depends(get_db),
) -> StructuredLectureResponse:
    """
    Retrieves the complete structured lecture payload with transcript segments,
    visual scenes, topic chapters, and synchronized timeline checkpoints.
    """
    cached = _STRUCTURED_LECTURE_CACHE.get(str(session_id))
    if cached:
        return cached

    structuring_service = LectureStructuringService(db=db, storage_service=storage_service)
    try:
        res = structuring_service.get_structured_lecture(session_id=session_id, db=db)
        _STRUCTURED_LECTURE_CACHE[str(session_id)] = res
        return res
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))



@router.get(
    "/sync-timeline/{session_id}",
    response_model=List[SyncPoint],
    summary="Get Multi-Track Synchronized Timeline",
)
def get_sync_timeline(
    session_id: UUID,
    db: Session = Depends(get_db),
) -> List[SyncPoint]:
    """
    Returns time-indexed checkpoints synchronizing speech text, speaker, visual modality, and slide deck index.
    """
    cached = _STRUCTURED_LECTURE_CACHE.get(str(session_id))
    if cached:
        return cached.synchronized_timeline

    structured = get_structured_lecture(session_id=session_id, db=db)
    return structured.synchronized_timeline


@router.get(
    "/topic-segments/{session_id}",
    response_model=List[TopicSegmentItem],
    summary="Get Semantic Topic Segments & Chapter Outline",
)
def get_topic_segments(
    session_id: UUID,
    db: Session = Depends(get_db),
) -> List[TopicSegmentItem]:
    """
    Returns the structured topic outline with chapter titles, summaries, and key concepts.
    """
    cached = _STRUCTURED_LECTURE_CACHE.get(str(session_id))
    if cached:
        return cached.topic_segments

    structured = get_structured_lecture(session_id=session_id, db=db)
    return structured.topic_segments
