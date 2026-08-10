"""
Teaching Intelligence API Router.
"""

from __future__ import annotations

import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response import ApiResponse, created, ok
from app.schemas.teaching import TeachingAnalyzeRequest
from app.services.teaching.teaching_service import TeachingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teaching", tags=["Teaching Intelligence"])


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
def analyze_teaching(
    payload: TeachingAnalyzeRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.analyze_lecture_teaching(payload)
        db.commit()
        msg = "Existing teaching analysis returned." if data.analysis_reused else "Teaching analysis completed."
        return created(data=data.model_dump(), message=msg, start_ts=start_ts)
    except Exception as exc:
        db.rollback()
        logger.exception("Error analyzing teaching for lecture_id=%s", payload.lecture_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/{lecture_id}")
def get_full_teaching_analysis(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_full_analysis(lecture_id)
        return ok(data=data.model_dump(), message="Teaching analysis retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{lecture_id}/summary")
def get_teaching_summary(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_summary(lecture_id)
        return ok(data=data.model_dump(), message="Teaching summary retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{lecture_id}/strengths")
def get_teaching_strengths(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_strengths(lecture_id)
        return ok(data=data.model_dump(), message="Teaching strengths retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{lecture_id}/weaknesses")
def get_teaching_weaknesses(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_weaknesses(lecture_id)
        return ok(data=data.model_dump(), message="Teaching weaknesses retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{lecture_id}/examples")
def get_teaching_examples(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_examples(lecture_id)
        return ok(data=data.model_dump(), message="Teaching examples retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{lecture_id}/interaction")
def get_teaching_interaction(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_interaction(lecture_id)
        return ok(data=data.model_dump(), message="Teaching interaction metrics retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{lecture_id}/structure")
def get_teaching_structure(
    lecture_id: UUID,
    db: Session = Depends(get_db),
) -> ApiResponse:
    start_ts = time.time()
    service = TeachingService(db)
    try:
        data = service.get_structure(lecture_id)
        return ok(data=data.model_dump(), message="Teaching structure metrics retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
