"""Read-only orchestration status for the teacher-facing AI workflow."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.coverage_summary import CoverageSummary
from app.models.explanation_engine import ExplanationSummary
from app.models.lecture_session import LectureSession
from app.models.recommendation_engine import RecAnalysis
from app.models.teaching_intelligence import TeachingSummary
from app.models.transcript import Transcript
from app.models.validation_summary import ValidationSummary
from app.schemas.response import ok

router = APIRouter(prefix="/workflow", tags=["AI Workflow"])


@router.get("/{lecture_id}/status", status_code=status.HTTP_200_OK, summary="Get AI workflow status")
def get_workflow_status(lecture_id: UUID, db: Annotated[Session, Depends(get_db)]) -> dict:
    """Returns record-existence flags without treating missing analysis as an HTTP error."""
    lecture = db.get(LectureSession, lecture_id)
    if lecture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    def exists(model):
        return db.execute(select(model.id).where(model.lecture_id == lecture_id).limit(1)).first() is not None  # type: ignore[attr-defined]

    data = {
        "lecture_id": str(lecture_id),
        "transcript_available": exists(Transcript),
        "coverage_ready": exists(CoverageSummary),
        "validation_ready": exists(ValidationSummary),
        "teaching_ready": exists(TeachingSummary),
        "recommendations_ready": db.execute(select(RecAnalysis.id).where(RecAnalysis.lecture_id == lecture_id, RecAnalysis.is_active.is_(True)).limit(1)).first() is not None,
        "explainability_ready": exists(ExplanationSummary),
    }
    return ok(data=data, message="AI workflow status retrieved.")
