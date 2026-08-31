"""Single durable coordinator for validation through explainability."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.coverage_summary import CoverageSummary
from app.models.explanation_engine import ExplanationSummary
from app.models.lecture_session import LectureSession
from app.models.recommendation_engine import RecAnalysis
from app.models.teaching_intelligence import TeachingSummary
from app.models.transcript import Transcript
from app.models.transcript_chunk import TranscriptChunk
from app.models.transcript_topic_mapping import TranscriptTopicMapping
from app.models.validation_summary import ValidationSummary
from app.schemas.teaching import TeachingAnalyzeRequest, TranscriptChunkItem
from app.services.coverage.coverage_service import CoverageService
from app.services.recommendation.recommendation_service import RecommendationService
from app.services.teaching.teaching_service import TeachingService
from app.services.validation.validation_service import ValidationService
from app.services.xai.explanation_api_service import ExplanationApiService

logger = logging.getLogger(__name__)
STAGES = ("validation", "coverage", "teaching", "recommendation", "explainability")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisExecutionService:
    """Creates idempotent jobs and invokes the existing engine services in order."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def start(self, lecture_id: UUID, curriculum_id: UUID, regenerate: bool = False) -> tuple[AnalysisJob, bool]:
        if self.db.get(LectureSession, lecture_id) is None:
            raise LookupError("Lecture not found")
        active = self.db.execute(
            select(AnalysisJob).where(AnalysisJob.lecture_id == lecture_id, AnalysisJob.status.in_(("PENDING", "PROCESSING"))).order_by(AnalysisJob.started_at.desc())
        ).scalars().first()
        if active:
            return active, False
        latest = self.db.execute(select(AnalysisJob).where(AnalysisJob.lecture_id == lecture_id).order_by(AnalysisJob.started_at.desc())).scalars().first()
        if latest and latest.status == "COMPLETED" and not regenerate:
            return latest, False
        job = AnalysisJob(lecture_id=lecture_id, curriculum_id=curriculum_id, status="PENDING", current_stage="QUEUED")
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job, True

    @staticmethod
    def status_data(job: AnalysisJob | None, lecture_id: UUID) -> dict:
        if job is None:
            return {"lecture_id": str(lecture_id), "overall_status": "NOT_STARTED", "validation_status": "PENDING", "coverage_status": "PENDING", "teaching_status": "PENDING", "recommendation_status": "PENDING", "explainability_status": "PENDING", "progress_percentage": 0, "current_stage": "NOT_STARTED", "estimated_remaining_seconds": 0, "job_id": None, "error_message": None}
        return {"lecture_id": str(job.lecture_id), "job_id": str(job.id), "overall_status": job.status, "validation_status": job.validation_status, "coverage_status": job.coverage_status, "teaching_status": job.teaching_status, "recommendation_status": job.recommendation_status, "explainability_status": job.explainability_status, "progress_percentage": job.progress_percentage, "current_stage": job.current_stage, "estimated_remaining_seconds": 0 if job.status in ("COMPLETED", "FAILED") else max(5, (100 - job.progress_percentage) * 2), "started_at": job.started_at.isoformat(), "error_message": job.error_message}


def run_analysis_job(job_id: UUID) -> None:
    """Background-task entry point; it deliberately owns a fresh database session."""
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None or job.status == "COMPLETED":
            return
        lecture = db.get(LectureSession, job.lecture_id)
        if lecture is None:
            raise LookupError("Lecture was deleted before analysis could start")
        chunks = _load_chunks(db, job.lecture_id)
        if not chunks:
            raise ValueError("No transcript chunks are available. Upload and process a transcript before analysis.")
        job.status, job.current_stage, job.progress_percentage = "PROCESSING", "VALIDATION", 5
        db.commit()
        _stage(db, job, "validation", 20, lambda: ValidationService(db).process_and_validate_transcript(chunks, job.lecture_id, job.curriculum_id, str(lecture.course_id), lecture.faculty_id))
        _stage(db, job, "coverage", 40, lambda: CoverageService(db).analyze_lecture_coverage(chunks, job.lecture_id, job.curriculum_id, str(lecture.course_id), lecture.faculty_id))
        _stage(db, job, "teaching", 60, lambda: TeachingService(db).analyze_lecture_teaching(TeachingAnalyzeRequest(lecture_id=job.lecture_id, curriculum_id=job.curriculum_id, faculty_id=lecture.faculty_id, transcript_chunks=[TranscriptChunkItem(**chunk) for chunk in chunks])))
        _stage(db, job, "recommendation", 80, lambda: RecommendationService(db).generate_recommendations(job.lecture_id, job.curriculum_id, lecture.faculty_id))
        _stage(db, job, "explainability", 95, lambda: ExplanationApiService(db).generate(job.lecture_id))
        _assert_persisted(db, job.lecture_id)
        job.status, job.current_stage, job.progress_percentage, job.completed_at = "COMPLETED", "COMPLETED", 100, _now()
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job:
            job.status, job.current_stage, job.error_message = "FAILED", "FAILED", str(exc)[:2000]
            db.commit()
        logger.exception("Analysis pipeline failed for job_id=%s", job_id)
    finally:
        db.close()


def _stage(db: Session, job: AnalysisJob, name: str, progress: int, action) -> None:
    setattr(job, f"{name}_status", "PROCESSING")
    job.current_stage, job.progress_percentage = name.upper(), progress - 15
    db.commit()
    action()
    db.commit()
    setattr(job, f"{name}_status", "COMPLETED")
    job.progress_percentage = progress
    db.commit()


def _load_chunks(db: Session, lecture_id: UUID | str, max_chunks: int = 500) -> list[dict]:
    lec_id_obj = UUID(str(lecture_id))
    rows = db.execute(
        select(TranscriptChunk)
        .join(Transcript, TranscriptChunk.transcript_id == Transcript.id)
        .where(Transcript.lecture_id == lec_id_obj)
        .order_by(TranscriptChunk.chunk_index)
        .limit(max_chunks)
    ).scalars().all()
    mappings = {mapping.chunk_id: mapping.topic_id for mapping in db.execute(select(TranscriptTopicMapping).where(TranscriptTopicMapping.lecture_id == lec_id_obj)).scalars()}
    return [{"chunk_id": str(chunk.id), "topic_id": str(mappings[chunk.id]) if mappings.get(chunk.id) else None, "speaker": chunk.speaker or "Faculty", "start_time": chunk.start_time, "end_time": chunk.end_time, "text": chunk.text} for chunk in rows]


def _assert_persisted(db: Session, lecture_id: UUID) -> None:
    checks = (ValidationSummary, CoverageSummary, TeachingSummary, ExplanationSummary)
    if any(db.execute(select(model.id).where(model.lecture_id == lecture_id).limit(1)).first() is None for model in checks):
        raise RuntimeError("Analysis finished without all required persisted result records")
    if db.execute(select(RecAnalysis.id).where(RecAnalysis.lecture_id == lecture_id, RecAnalysis.is_active.is_(True)).limit(1)).first() is None:
        raise RuntimeError("Recommendation analysis was not persisted")
