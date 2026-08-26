"""
Media Job Service — Orchestrates background audio/video processing jobs.
Creates DB job records, runs the actual AI pipelines in the background,
and updates progress so the frontend can poll for status.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.media_processing_job import MediaProcessingJob
from app.schemas.job import JobStatusResponse, SessionJobsResponse

logger = logging.getLogger(__name__)


class MediaJobService:
    """Creates, runs, and tracks async audio/video processing jobs."""

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────────────────────────────────────
    # Job Creation
    # ─────────────────────────────────────────────────────────────────────────

    def create_job(
        self,
        session_id: UUID,
        job_type: str = "audio_process",
        config_snapshot: Optional[dict] = None,
    ) -> MediaProcessingJob:
        """Creates a new PENDING job record and returns it."""
        job = MediaProcessingJob(
            session_id=session_id,
            job_type=job_type,
            status="PENDING",
            progress=0,
            config_snapshot=json.dumps(config_snapshot or {}),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logger.info("Created %s job %s for session %s", job_type, job.id, session_id)
        return job

    # ─────────────────────────────────────────────────────────────────────────
    # Background Workers (called by FastAPI BackgroundTasks)
    # ─────────────────────────────────────────────────────────────────────────

    def run_audio_job(
        self,
        job_id: UUID,
        session_id: UUID,
        domain_subject: str = "auto",
        domain_vocabulary: Optional[List[str]] = None,
        language: str = "auto",
        model_size: str = "base",
        diarization_mode: str = "lecture",
        boost_audio_volume: bool = True,
        enable_vad: bool = True,
        enable_diarization: bool = True,
        sync_academic: bool = True,
    ) -> None:
        """
        Runs the full Audio Intelligence pipeline in a background thread.
        Updates the job record with progress and final result.
        Must create its own DB session since FastAPI closes the request session
        when BackgroundTasks run after the response is sent.
        """
        from app.db.session import SessionLocal
        from app.services.audio.audio_intelligence_service import AudioIntelligenceService
        from app.services.multimedia.storage_service import MultimediaStorageService

        bg_db = SessionLocal()
        try:
            self._set_running(bg_db, job_id, progress=5)

            service = AudioIntelligenceService(
                db=bg_db,
                storage_service=MultimediaStorageService(),
            )

            self._set_running(bg_db, job_id, progress=20)

            result = service.process_session_audio(
                session_id=session_id,
                domain_subject=domain_subject,
                domain_vocabulary=domain_vocabulary,
                language=language,
                model_size=model_size,
                diarization_mode=diarization_mode,
                boost_audio_volume=boost_audio_volume,
                enable_vad=enable_vad,
                enable_diarization=enable_diarization,
                sync_academic=sync_academic,
            )

            self._set_running(bg_db, job_id, progress=90)

            # Store a lightweight summary (not full segments — those are in DB/disk)
            summary = {
                "status": result.status,
                "total_words": result.total_words,
                "total_segments": result.total_segments,
                "language": result.language,
                "duration_seconds": result.duration_seconds,
                "academic_synced": result.academic_synced,
                "teacher_talk_ratio": result.diarization_summary.teacher_talk_ratio
                if result.diarization_summary
                else None,
            }

            self._set_completed(bg_db, job_id, result_summary=summary)
            logger.info("Audio job %s completed for session %s", job_id, session_id)

        except Exception as exc:
            logger.exception("Audio job %s FAILED for session %s: %s", job_id, session_id, exc)
            self._set_failed(bg_db, job_id, error=str(exc))
        finally:
            bg_db.close()

    def run_video_job(
        self,
        job_id: UUID,
        session_id: UUID,
        sample_interval_sec: float = 5.0,
        detect_teacher: bool = True,
        detect_board: bool = True,
        detect_ppt: bool = True,
        min_scene_duration_sec: float = 3.0,
    ) -> None:
        """Runs the full Video Intelligence pipeline in a background thread."""
        from app.db.session import SessionLocal
        from app.schemas.video import VideoProcessRequest
        from app.services.multimedia.storage_service import MultimediaStorageService
        from app.services.video.video_intelligence_service import VideoIntelligenceService

        bg_db = SessionLocal()
        try:
            self._set_running(bg_db, job_id, progress=5)

            service = VideoIntelligenceService(
                storage_service=MultimediaStorageService(),
            )

            config = VideoProcessRequest(
                sample_interval_sec=sample_interval_sec,
                detect_teacher=detect_teacher,
                detect_board=detect_board,
                detect_ppt=detect_ppt,
                min_scene_duration_sec=min_scene_duration_sec,
            )

            self._set_running(bg_db, job_id, progress=25)

            result = service.process_session_video(session_id=session_id, request_config=config)

            self._set_running(bg_db, job_id, progress=90)

            summary = {
                "status": result.status,
                "total_duration_sec": result.summary.total_duration_sec,
                "analyzed_frames_count": result.summary.analyzed_frames_count,
                "teacher_presence_ratio": result.summary.teacher_presence_ratio,
                "board_writing_ratio": result.summary.board_writing_ratio,
                "ppt_presentation_ratio": result.summary.ppt_presentation_ratio,
                "timeline_events_count": result.summary.timeline_events_count,
            }

            self._set_completed(bg_db, job_id, result_summary=summary)
            logger.info("Video job %s completed for session %s", job_id, session_id)

        except Exception as exc:
            logger.exception("Video job %s FAILED for session %s: %s", job_id, session_id, exc)
            self._set_failed(bg_db, job_id, error=str(exc))
        finally:
            bg_db.close()

    def run_full_pipeline_job(
        self,
        job_id: UUID,
        session_id: UUID,
        audio_options: Optional[dict] = None,
        video_options: Optional[dict] = None,
    ) -> None:
        """Runs audio + video pipelines sequentially in one background job."""
        from app.db.session import SessionLocal
        from app.schemas.video import VideoProcessRequest
        from app.services.audio.audio_intelligence_service import AudioIntelligenceService
        from app.services.multimedia.storage_service import MultimediaStorageService
        from app.services.video.video_intelligence_service import VideoIntelligenceService

        ao = audio_options or {}
        vo = video_options or {}
        bg_db = SessionLocal()
        try:
            self._set_running(bg_db, job_id, progress=5)
            storage = MultimediaStorageService()

            # Stage 1 — Audio
            audio_svc = AudioIntelligenceService(db=bg_db, storage_service=storage)
            audio_result = audio_svc.process_session_audio(
                session_id=session_id,
                domain_subject=ao.get("domain_subject", "auto"),
                language=ao.get("language", "auto"),
                model_size=ao.get("model_size", "base"),
                diarization_mode=ao.get("diarization_mode", "lecture"),
                enable_vad=ao.get("enable_vad", True),
                enable_diarization=ao.get("enable_diarization", True),
                sync_academic=ao.get("sync_academic", True),
            )
            self._set_running(bg_db, job_id, progress=60)

            # Stage 2 — Video
            video_svc = VideoIntelligenceService(storage_service=storage)
            config = VideoProcessRequest(
                sample_interval_sec=vo.get("sample_interval_sec", 5.0),
                detect_teacher=vo.get("detect_teacher", True),
                detect_board=vo.get("detect_board", True),
                detect_ppt=vo.get("detect_ppt", True),
            )
            video_result = video_svc.process_session_video(
                session_id=session_id, request_config=config
            )
            self._set_running(bg_db, job_id, progress=95)

            summary = {
                "audio": {
                    "total_words": audio_result.total_words,
                    "total_segments": audio_result.total_segments,
                    "academic_synced": audio_result.academic_synced,
                },
                "video": {
                    "analyzed_frames": video_result.summary.analyzed_frames_count,
                    "timeline_events": video_result.summary.timeline_events_count,
                },
            }
            self._set_completed(bg_db, job_id, result_summary=summary)
            logger.info("Full pipeline job %s completed for session %s", job_id, session_id)

        except Exception as exc:
            logger.exception("Full pipeline job %s FAILED: %s", job_id, exc)
            self._set_failed(bg_db, job_id, error=str(exc))
        finally:
            bg_db.close()

    # ─────────────────────────────────────────────────────────────────────────
    # Job Query
    # ─────────────────────────────────────────────────────────────────────────

    def get_job(self, job_id: UUID) -> Optional[MediaProcessingJob]:
        return self.db.get(MediaProcessingJob, job_id)

    def get_session_jobs(self, session_id: UUID) -> List[MediaProcessingJob]:
        return (
            self.db.query(MediaProcessingJob)
            .filter(MediaProcessingJob.session_id == session_id)
            .order_by(MediaProcessingJob.created_at.desc())
            .all()
        )

    def to_status_response(self, job: MediaProcessingJob) -> JobStatusResponse:
        result_summary = None
        if job.result_summary:
            try:
                result_summary = json.loads(job.result_summary)
            except Exception:
                pass
        return JobStatusResponse(
            job_id=job.id,
            session_id=job.session_id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            result_summary=result_summary,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Internal State Transitions
    # ─────────────────────────────────────────────────────────────────────────

    def _set_running(self, db: Session, job_id: UUID, progress: int = 10) -> None:
        job = db.get(MediaProcessingJob, job_id)
        if job:
            job.status = "RUNNING"
            job.progress = progress
            db.commit()

    def _set_completed(
        self, db: Session, job_id: UUID, result_summary: Optional[dict] = None
    ) -> None:
        job = db.get(MediaProcessingJob, job_id)
        if job:
            job.status = "COMPLETED"
            job.progress = 100
            job.completed_at = datetime.now(timezone.utc)
            if result_summary:
                job.result_summary = json.dumps(result_summary)
            db.commit()

    def _set_failed(self, db: Session, job_id: UUID, error: str = "") -> None:
        job = db.get(MediaProcessingJob, job_id)
        if job:
            job.status = "FAILED"
            job.error_message = error[:2000]  # cap at 2000 chars
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
