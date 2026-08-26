"""
REST API Router for Audio Intelligence & Speech Processing (Module 2).
Prefix: /api/v1/audio

Processing endpoints now return a job_id immediately so long lectures
don't block the HTTP connection. Use GET /jobs/{job_id} to poll status.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Annotated, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audio import (
    AudioProcessRequest,
    AudioTranscriptResponse,
)
from app.schemas.job import JobSubmitResponse
from app.schemas.response import ok
from app.services.audio.audio_intelligence_service import AudioIntelligenceService
from app.services.audio.whisper_engine import WhisperEngine
from app.services.job_service import MediaJobService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audio", tags=["Audio Intelligence & Speech-to-Text"])


@router.post(
    "/session/{session_id}/process",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit lecture audio for async Speech Intelligence processing",
    description=(
        "Submits a background job for Voice Activity Detection (VAD), Whisper STT, "
        "speaker diarization, PostgreSQL persistence, and Academic Intelligence sync. "
        "Returns a job_id immediately — poll GET /api/v1/jobs/{job_id} for progress. "
        "Results are available via GET /api/v1/audio/session/{id}/transcript once COMPLETED."
    ),
)
def process_audio(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    payload: Optional[AudioProcessRequest] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    start_ts = time.time()

    vocab = payload.domain_vocabulary if payload else None
    subject = payload.domain_subject if payload else "auto"
    lang = payload.language if payload else "auto"
    m_size = payload.model_size if payload else "base"
    diar_mode = payload.diarization_mode if payload else "lecture"
    boost_vol = payload.boost_audio_volume if payload else True
    enable_vad = payload.enable_vad if payload else True
    enable_diar = payload.enable_diarization if payload else True
    sync_acad = payload.sync_academic if payload else True

    # Create the job record (PENDING) — this is the only DB write in the request
    svc = MediaJobService(db)
    config_snapshot = {
        "domain_subject": subject,
        "language": lang,
        "model_size": m_size,
        "diarization_mode": diar_mode,
        "enable_vad": enable_vad,
        "enable_diarization": enable_diar,
        "sync_academic": sync_acad,
    }
    try:
        job = svc.create_job(
            session_id=session_id,
            job_type="audio_process",
            config_snapshot=config_snapshot,
        )
    except Exception as exc:
        logger.exception("Failed to create audio job for session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not queue audio processing job: {exc}",
        ) from exc

    # Kick off background processing — response is sent BEFORE this runs
    background_tasks.add_task(
        svc.run_audio_job,
        job_id=job.id,
        session_id=session_id,
        domain_subject=subject,
        domain_vocabulary=vocab,
        language=lang,
        model_size=m_size,
        diarization_mode=diar_mode,
        boost_audio_volume=boost_vol,
        enable_vad=enable_vad,
        enable_diarization=enable_diar,
        sync_academic=sync_acad,
    )

    response = JobSubmitResponse(
        job_id=job.id,
        session_id=session_id,
        job_type="audio_process",
        status="PENDING",
        message=(
            f"Audio processing job queued. "
            f"Using Whisper '{m_size}' model with '{diar_mode}' diarization mode. "
            f"Poll the job status URL for real-time progress."
        ),
        poll_url=f"/api/v1/jobs/{job.id}",
    )
    return ok(data=response.model_dump(mode="json"), message="Audio job accepted.", start_ts=start_ts)


@router.get(
    "/session/{session_id}/transcript",
    status_code=status.HTTP_200_OK,
    summary="Get diarized timestamped transcript for a session",
    description=(
        "Retrieves the full transcript with speaker labels (Teacher vs Student), "
        "timestamps, confidence scores, and interaction ratios. "
        "Returns has_transcript=False if processing has not completed yet."
    ),
)
def get_transcript(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = AudioIntelligenceService(db)
    res = service.get_session_transcript(session_id)
    return ok(data=res.model_dump(mode="json"), message="Transcript retrieved.", start_ts=start_ts)


@router.get(
    "/session/{session_id}/job-status",
    status_code=status.HTTP_200_OK,
    summary="Get the latest audio processing job status for a session",
    description="Convenience endpoint — returns the most recent audio job status for a session without needing the job_id.",
)
def get_session_audio_job_status(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    svc = MediaJobService(db)
    jobs = svc.get_session_jobs(session_id)
    audio_jobs = [j for j in jobs if j.job_type in {"audio_process", "full_pipeline"}]
    if not audio_jobs:
        return ok(
            data={"session_id": str(session_id), "status": "NOT_STARTED", "jobs": []},
            message="No audio processing jobs found for this session.",
            start_ts=start_ts,
        )
    latest = audio_jobs[0]
    return ok(
        data=svc.to_status_response(latest).model_dump(mode="json"),
        message="Latest audio job status retrieved.",
        start_ts=start_ts,
    )


@router.post(
    "/session/{session_id}/process-sync",
    status_code=status.HTTP_200_OK,
    summary="[SYNC] Process lecture audio — blocking (for testing/dev only)",
    description=(
        "Synchronous version of the audio processing endpoint. "
        "Blocks until Whisper finishes — use only for short clips or automated tests. "
        "For real lectures, use POST /process (async) instead."
    ),
)
def process_audio_sync(
    session_id: UUID,
    payload: Optional[AudioProcessRequest] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    """Kept for test suite compatibility — tests use this to verify transcription without polling."""
    start_ts = time.time()
    service = AudioIntelligenceService(db)
    try:
        vocab = payload.domain_vocabulary if payload else None
        subject = payload.domain_subject if payload else "auto"
        lang = payload.language if payload else "auto"
        m_size = payload.model_size if payload else "base"
        diar_mode = payload.diarization_mode if payload else "lecture"
        boost_vol = payload.boost_audio_volume if payload else True
        enable_vad = payload.enable_vad if payload else True
        enable_diar = payload.enable_diarization if payload else True
        sync_acad = payload.sync_academic if payload else True

        res = service.process_session_audio(
            session_id=session_id,
            domain_subject=subject,
            domain_vocabulary=vocab,
            language=lang,
            model_size=m_size,
            diarization_mode=diar_mode,
            boost_audio_volume=boost_vol,
            enable_vad=enable_vad,
            enable_diarization=enable_diar,
            sync_academic=sync_acad,
        )
        return ok(data=res.model_dump(mode="json"), message="Audio transcribed and diarized successfully.", start_ts=start_ts)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Sync audio processing failed for session %s", session_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/transcribe-file",
    status_code=status.HTTP_200_OK,
    summary="Standalone audio/video file transcription",
    description=(
        "Directly transcribes an uploaded audio or video file using Whisper STT. "
        "Accepts WAV, MP3, M4A, AAC, OGG, FLAC, MP4, WebM, MKV. "
        "Non-WAV formats are automatically converted to 16kHz mono WAV before Whisper processing."
    ),
)
async def transcribe_audio_file(
    audio_file: Annotated[UploadFile, File(description="Audio or video file to transcribe (WAV, MP3, M4A, MP4, WebM, etc.)")],
) -> dict:
    start_ts = time.time()
    whisper = WhisperEngine()
    import tempfile
    suffix = Path(audio_file.filename or "audio.wav").suffix.lower() or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio_file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    wav_path: Optional[Path] = None
    try:
        # Convert non-WAV formats to 16kHz mono WAV for reliable Whisper processing
        if suffix not in {".wav"}:
            from app.services.multimedia.ffmpeg_processor import FFmpegProcessor
            ffmpeg = FFmpegProcessor()
            wav_path = tmp_path.with_suffix(".converted.wav")
            try:
                ffmpeg.extract_audio_16k_mono(tmp_path, wav_path)
                process_path = wav_path if (wav_path.exists() and wav_path.stat().st_size > 0) else tmp_path
            except Exception:
                process_path = tmp_path
        else:
            process_path = tmp_path

        segments = whisper.transcribe_audio(process_path)
        return ok(data={"filename": audio_file.filename, "segments": segments}, message="Transcription complete.", start_ts=start_ts)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
        if wav_path and wav_path.exists():
            wav_path.unlink()
