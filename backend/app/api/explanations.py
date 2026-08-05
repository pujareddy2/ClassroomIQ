"""REST API router for the Explainable AI (XAI) trust layer.

All frontend explainability reads and writes must use this router so the
UI never talks to database tables directly. The router stays thin and
delegates to the existing service/repository stack via the API facade.
"""

from __future__ import annotations

import logging
import time
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.exceptions.xai_exceptions import DuplicateExplanationError, ExplanationNotFoundError
from app.schemas.explanation import ExplainGenerateRequest
from app.schemas.response import created, ok, paginated
from app.services.xai.explanation_api_service import ExplanationApiService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/explanations", tags=["Explainable AI"])


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Generate an explainability package for a lecture",
    description="Builds and persists the XAI explanation package using the existing service/repository stack.",
)
def generate_explanation(
    payload: ExplainGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.generate(payload.lecture_id)
        db.commit()
        return created(data=result, message="Explainability package generated.", start_ts=start)
    except DuplicateExplanationError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error generating explanation package")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full explainability package for a lecture",
)
def get_explanation_package(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_package(lecture_id)
        return ok(data=result, message="Explainability package retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation package")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/summary",
    status_code=status.HTTP_200_OK,
    summary="Get lecture-level explainability summary",
)
def get_explanation_summary(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_summary(lecture_id)
        return ok(data=result, message="Explainability summary retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation summary")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/evidence",
    status_code=status.HTTP_200_OK,
    summary="Get paginated evidence items for a lecture",
)
def get_explanation_evidence(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Optional[str] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    search: Optional[str] = Query(default=None),
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_evidence(lecture_id, page, page_size, sort or "", order, search)
        return paginated(result["items"], result["pagination"], message="Evidence retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation evidence")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/transcripts",
    status_code=status.HTTP_200_OK,
    summary="Get transcript evidence snippets for a lecture",
)
def get_explanation_transcripts(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Optional[str] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    search: Optional[str] = Query(default=None),
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_transcripts(lecture_id, page, page_size, sort or "", order, search)
        return paginated(result["items"], result["pagination"], message="Transcript evidence retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation transcripts")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/citations",
    status_code=status.HTTP_200_OK,
    summary="Get citation evidence for a lecture",
)
def get_explanation_citations(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Optional[str] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    search: Optional[str] = Query(default=None),
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_citations(lecture_id, page, page_size, sort or "", order, search)
        return paginated(result["items"], result["pagination"], message="Citations retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation citations")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/confidence",
    status_code=status.HTTP_200_OK,
    summary="Get confidence breakdowns for a lecture",
)
def get_explanation_confidence(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Optional[str] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    search: Optional[str] = Query(default=None),
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_confidence(lecture_id, page, page_size, sort or "", order, search)
        return paginated(result["items"], result["pagination"], message="Confidence data retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation confidence")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/reasoning",
    status_code=status.HTTP_200_OK,
    summary="Get ordered reasoning steps for a lecture",
)
def get_explanation_reasoning(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Optional[str] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    search: Optional[str] = Query(default=None),
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_reasoning(lecture_id, page, page_size, sort or "", order, search)
        return paginated(result["items"], result["pagination"], message="Reasoning steps retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation reasoning")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/timeline",
    status_code=status.HTTP_200_OK,
    summary="Get explanation timeline entries for a lecture",
)
def get_explanation_timeline(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: Optional[str] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    search: Optional[str] = Query(default=None),
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_timeline(lecture_id, page, page_size, sort or "", order, search)
        return paginated(result["items"], result["pagination"], message="Timeline retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation timeline")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/decisions/{decision_id}",
    status_code=status.HTTP_200_OK,
    summary="Get one explainability decision record",
)
def get_explanation_decision(
    lecture_id: UUID,
    decision_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start = time.time()
    service = ExplanationApiService(db)
    try:
        result = service.get_decision(lecture_id, decision_id)
        return ok(data=result, message="Decision explanation retrieved.", start_ts=start)
    except ExplanationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching explanation decision")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
