"""Asynchronous REST API for the centralized Member 2 analysis pipeline."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.analysis_job import AnalysisJob
from app.schemas.analysis import AnalysisRunRequest
from app.schemas.response import created, ok
from app.services.analysis_execution_service import AnalysisExecutionService, run_analysis_job

router = APIRouter(prefix="/analysis", tags=["AI Analysis Execution"])


@router.post("/run", status_code=status.HTTP_202_ACCEPTED, summary="Run the complete lecture AI analysis", description="Queues the persisted Validation → Coverage → Teaching → Recommendations → Explainability pipeline. Repeated requests reuse the active or completed job.")
def run_analysis(payload: AnalysisRunRequest, background_tasks: BackgroundTasks, db: Annotated[Session, Depends(get_db)]) -> dict:
    try:
        job, scheduled = AnalysisExecutionService(db).start(payload.lecture_id, payload.curriculum_id, payload.regenerate)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if scheduled:
        background_tasks.add_task(run_analysis_job, job.id)
    return created(data=AnalysisExecutionService.status_data(job, payload.lecture_id), message="Analysis execution queued." if scheduled else "Existing analysis execution reused.")


@router.get("/status/{lecture_id}", summary="Get centralized lecture analysis status", description="The only polling endpoint for the AI pages. It never triggers engine execution.")
def get_analysis_status(lecture_id: UUID, db: Annotated[Session, Depends(get_db)]) -> dict:
    job = db.execute(select(AnalysisJob).where(AnalysisJob.lecture_id == lecture_id).order_by(AnalysisJob.started_at.desc())).scalars().first()
    return ok(data=AnalysisExecutionService.status_data(job, lecture_id), message="Analysis execution status retrieved.")
