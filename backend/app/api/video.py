"""
REST API Router for Video Intelligence & OpenCV Processing (Module 3).
Prefix: /api/v1/video

Processing endpoints return a job_id immediately.
Poll GET /api/v1/jobs/{job_id} for status.
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobSubmitResponse
from app.schemas.response import ok
from app.schemas.video import (
    VideoIntelligenceSummary,
    VideoProcessRequest,
    VideoProcessResponse,
    VisualTimelineEvent,
)
from app.services.job_service import MediaJobService
from app.services.multimedia.storage_service import MultimediaStorageService
from app.services.video.video_intelligence_service import VideoIntelligenceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video", tags=["Video Intelligence"])

video_service = VideoIntelligenceService()
storage_service = MultimediaStorageService()

# In-memory cache for fast retrieval by GET endpoints
_SESSION_VIDEO_CACHE: Dict[str, VideoProcessResponse] = {}


@router.post(
    "/process/{session_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit lecture video for async Video Intelligence processing",
    description=(
        "Submits a background job for OpenCV frame extraction, teacher detection, "
        "board/PPT analysis, and visual timeline construction. "
        "Returns a job_id immediately — poll GET /api/v1/jobs/{job_id} for progress. "
        "Results available via GET /api/v1/video/timeline/{id} once COMPLETED."
    ),
)
def process_session_video(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    request: Optional[VideoProcessRequest] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    start_ts = time.time()
    cfg = request or VideoProcessRequest()

    svc = MediaJobService(db)
    config_snapshot = {
        "sample_interval_sec": cfg.sample_interval_sec,
        "detect_teacher": cfg.detect_teacher,
        "detect_board": cfg.detect_board,
        "detect_ppt": cfg.detect_ppt,
        "min_scene_duration_sec": cfg.min_scene_duration_sec,
    }
    try:
        job = svc.create_job(
            session_id=session_id,
            job_type="video_process",
            config_snapshot=config_snapshot,
        )
    except Exception as exc:
        logger.exception("Failed to create video job for session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not queue video processing job: {exc}",
        ) from exc

    background_tasks.add_task(
        svc.run_video_job,
        job_id=job.id,
        session_id=session_id,
        sample_interval_sec=cfg.sample_interval_sec,
        detect_teacher=cfg.detect_teacher,
        detect_board=cfg.detect_board,
        detect_ppt=cfg.detect_ppt,
        min_scene_duration_sec=cfg.min_scene_duration_sec,
    )

    response = JobSubmitResponse(
        job_id=job.id,
        session_id=session_id,
        job_type="video_process",
        status="PENDING",
        message=(
            f"Video intelligence job queued. "
            f"Sampling every {cfg.sample_interval_sec}s with teacher/board/PPT detection. "
            f"Poll the job status URL for real-time progress."
        ),
        poll_url=f"/api/v1/jobs/{job.id}",
    )
    return ok(data=response.model_dump(mode="json"), message="Video job accepted.", start_ts=start_ts)


@router.post(
    "/process-full/{session_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit full Audio + Video pipeline as a single async job",
    description=(
        "Runs audio transcription then video analysis sequentially in one background job. "
        "Ideal for kicking off complete lecture processing in one API call."
    ),
)
def process_full_pipeline(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    start_ts = time.time()
    svc = MediaJobService(db)
    try:
        job = svc.create_job(
            session_id=session_id,
            job_type="full_pipeline",
            config_snapshot={"mode": "audio_then_video"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not queue full pipeline job: {exc}",
        ) from exc

    background_tasks.add_task(
        svc.run_full_pipeline_job,
        job_id=job.id,
        session_id=session_id,
    )

    response = JobSubmitResponse(
        job_id=job.id,
        session_id=session_id,
        job_type="full_pipeline",
        status="PENDING",
        message="Full pipeline (audio + video) job queued.",
        poll_url=f"/api/v1/jobs/{job.id}",
    )
    return ok(data=response.model_dump(mode="json"), message="Full pipeline job accepted.", start_ts=start_ts)


@router.post(
    "/analyze-file",
    response_model=VideoProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Standalone Video Analysis for Uploaded Media",
    description=(
        "Directly uploads a standalone video and generates full visual scene classification and keyframes. "
        "This endpoint is synchronous (for short test clips or demo videos)."
    ),
)
async def analyze_video_file(
    video_file: UploadFile = File(..., description="Classroom video file (MP4, WebM, MKV, AVI)"),
    sample_interval_sec: float = Form(5.0),
    detect_teacher: bool = Form(True),
    detect_board: bool = Form(True),
    detect_ppt: bool = Form(True),
) -> VideoProcessResponse:
    temp_dir = Path(tempfile.mkdtemp(prefix="video_analysis_"))
    temp_video_path = temp_dir / (video_file.filename or "input_video.mp4")
    keyframes_dir = temp_dir / "keyframes"

    try:
        content = await video_file.read()
        temp_video_path.write_bytes(content)

        config = VideoProcessRequest(
            sample_interval_sec=sample_interval_sec,
            detect_teacher=detect_teacher,
            detect_board=detect_board,
            detect_ppt=detect_ppt,
        )

        response = video_service.process_video_file(
            video_path=temp_video_path,
            output_keyframes_dir=keyframes_dir,
            config=config,
        )
        return response
    except Exception as exc:
        logger.exception("Standalone video file analysis failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video file analysis failed: {str(exc)}",
        )


@router.get(
    "/timeline/{session_id}",
    response_model=List[VisualTimelineEvent],
    summary="Get Visual Lecture Timeline Events",
)
def get_visual_timeline(session_id: UUID) -> List[VisualTimelineEvent]:
    """Fetches the chronological visual event stream for a session."""
    cached = _SESSION_VIDEO_CACHE.get(str(session_id))
    if cached:
        return cached.timeline

    res = video_service.get_session_video(session_id)
    return res.timeline


@router.get(
    "/summary/{session_id}",
    response_model=VideoIntelligenceSummary,
    summary="Get Video Analytics Summary & Visual Metrics",
)
def get_visual_summary(session_id: UUID) -> VideoIntelligenceSummary:
    """Fetches high-level visual analytics (Teacher presence %, Board writing %, PPT %)."""
    cached = _SESSION_VIDEO_CACHE.get(str(session_id))
    if cached:
        return cached.summary

    res = video_service.get_session_video(session_id)
    return res.summary


@router.get(
    "/keyframe/{session_id}/{filename}",
    summary="Stream Extracted Keyframe Image",
)
def get_keyframe_image(session_id: UUID, filename: str) -> FileResponse:
    """Streams a specific extracted keyframe JPEG image for the session player."""
    session_dir = storage_service.get_session_dir(session_id)
    keyframe_path = session_dir / "keyframes" / filename

    if not keyframe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Keyframe {filename} not found")

    return FileResponse(path=str(keyframe_path), media_type="image/jpeg")
