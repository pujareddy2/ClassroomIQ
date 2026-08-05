"""
REST API router for Recommendation Engine Module.

Routes:
  POST /recommendations/generate
  GET  /recommendations/{lecture_id}
  GET  /recommendations/{lecture_id}/priority
  GET  /recommendations/{lecture_id}/evidence
  GET  /recommendations/faculty/{faculty_id}/weekly
  GET  /recommendations/faculty/{faculty_id}/monthly
  GET  /recommendations/faculty/{faculty_id}/history
"""

import logging
import time
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.recommendation import (
    MonthlySummaryResponse,
    PriorityBreakdownResponse,
    RecommendationGenerateData,
    RecommendationGenerateRequest,
    WeeklySummaryResponse,
)
from app.schemas.response import created, ok
from app.services.recommendation.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])


@router.post(
    "/generate",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
)
def generate_recommendations(
    payload: RecommendationGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    POST /recommendations/generate

    Transforms coverage, validation, and teaching intelligence facts into
    actionable, prioritized recommendations with professional faculty feedback.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        result = service.generate_recommendations(
            lecture_id=payload.lecture_id,
            curriculum_id=payload.curriculum_id,
            faculty_id=payload.faculty_id,
            force_reanalyze=payload.force_reanalyze,
        )
        return created(data=result, message="Recommendations generated successfully.", start_ts=start)
    except Exception as exc:
        logger.exception("Unexpected error generating recommendations")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/{lecture_id}",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_recommendations_for_lecture(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /recommendations/{lecture_id}

    Returns all active recommendations for a given lecture.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        result = service.get_recommendations_for_lecture(lecture_id)
        return ok(data=result, message="Recommendations retrieved successfully.", start_ts=start)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching recommendations for lecture")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/{lecture_id}/priority",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_recommendations_by_priority(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /recommendations/{lecture_id}/priority

    Returns recommendations for a lecture ordered descending by priority score.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        items = service.get_recommendations_by_priority(lecture_id)
        return ok(data=items, message="Priority recommendations retrieved.", start_ts=start)
    except Exception as exc:
        logger.exception("Unexpected error fetching priority recommendations")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/{lecture_id}/evidence",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_recommendation_evidence(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /recommendations/{lecture_id}/evidence

    Returns supporting evidence items linked to active recommendations.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        evidence = service.get_evidence_for_lecture(lecture_id)
        return ok(data=evidence, message="Supporting evidence retrieved.", start_ts=start)
    except Exception as exc:
        logger.exception("Unexpected error fetching recommendation evidence")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/faculty/{faculty_id}/weekly",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_weekly_recommendation_summary(
    faculty_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    week_label: str = "2026-W31",
):
    """
    GET /recommendations/faculty/{faculty_id}/weekly

    Returns aggregated weekly recommendation summary for a faculty member.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        weekly = service.get_weekly_summary(faculty_id, week_label)
        data = {
            "faculty_id": str(weekly.faculty_id),
            "week_label": weekly.week_label,
            "lecture_count": weekly.lecture_count,
            "total_recommendations": weekly.total_recommendations,
            "critical_count": weekly.critical_count,
            "high_count": weekly.high_count,
            "medium_count": weekly.medium_count,
            "low_count": weekly.low_count,
            "repeated_weaknesses": weekly.repeated_weaknesses or [],
            "improving_areas": weekly.improving_areas or [],
            "declining_areas": weekly.declining_areas or [],
            "frequently_skipped_topics": weekly.frequently_skipped_topics or [],
            "frequently_incorrect_concepts": weekly.frequently_incorrect_concepts or [],
            "avg_coverage_score": weekly.avg_coverage_score,
            "avg_validation_score": weekly.avg_validation_score,
            "avg_teaching_score": weekly.avg_teaching_score,
            "summary_text": weekly.summary_text,
        }
        return ok(data=data, message="Weekly recommendation summary retrieved.", start_ts=start)
    except Exception as exc:
        logger.exception("Unexpected error fetching weekly recommendation summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/faculty/{faculty_id}/monthly",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_monthly_recommendation_summary(
    faculty_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    month_label: str = "2026-08",
):
    """
    GET /recommendations/faculty/{faculty_id}/monthly

    Returns aggregated monthly recommendation progress report for a faculty member.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        monthly = service.get_monthly_summary(faculty_id, month_label)
        data = {
            "faculty_id": str(monthly.faculty_id),
            "month_label": monthly.month_label,
            "week_count": monthly.week_count,
            "lecture_count": monthly.lecture_count,
            "total_recommendations": monthly.total_recommendations,
            "coverage_trend": monthly.coverage_trend or [],
            "validation_trend": monthly.validation_trend or [],
            "teaching_trend": monthly.teaching_trend or [],
            "interaction_trend": monthly.interaction_trend or [],
            "overall_progress_score": monthly.overall_progress_score,
            "monthly_improvement_report": monthly.monthly_improvement_report,
            "top_recurring_issues": monthly.top_recurring_issues or [],
            "most_improved_areas": monthly.most_improved_areas or [],
        }
        return ok(data=data, message="Monthly recommendation summary retrieved.", start_ts=start)
    except Exception as exc:
        logger.exception("Unexpected error fetching monthly recommendation summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/faculty/{faculty_id}/history",
    response_model=None,
    status_code=status.HTTP_200_OK,
)
def get_recommendation_history(
    faculty_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    """
    GET /recommendations/faculty/{faculty_id}/history

    Returns recommendation analysis history for a faculty member.
    """
    start = time.time()
    service = RecommendationService(db)
    try:
        history = service.get_faculty_history(faculty_id)
        return ok(data=history, message="Recommendation history retrieved.", start_ts=start)
    except Exception as exc:
        logger.exception("Unexpected error fetching recommendation history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
