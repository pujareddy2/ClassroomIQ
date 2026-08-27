"""
REST API Router for Lecture Capture & Multimedia Intelligence (Module 1).
Prefix: /api/v1/multimedia
"""

from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path
from typing import Annotated, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.multimedia import (
    ChunkUploadResponse,
    LectureUploadResponse,
    SessionCompleteRequest,
    SessionCompleteResponse,
    SessionDetailResponse,
    SessionInitRequest,
    SessionInitResponse,
    SessionListResponse,
)
from app.schemas.response import created, ok
from app.services.multimedia.capture_service import CaptureService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/multimedia", tags=["Multimedia & Lecture Capture"])


@router.post(
    "/session/start",
    status_code=status.HTTP_201_CREATED,
    summary="Start a live lecture recording session",
    description="Initializes a new live classroom recording session in the database and prepares storage buffers.",
)
def start_session(
    payload: SessionInitRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)
    try:
        res = service.init_live_session(
            course_name_or_code=payload.course_name_or_code,
            faculty_name=payload.faculty_name or "Faculty",
            title=payload.title or "Classroom Lecture",
            classroom=payload.classroom,
            consent_confirmed=payload.consent_confirmed,
            has_screen_share=payload.has_screen_share,
        )
        return created(data=res.model_dump(mode="json"), message="Recording session started.", start_ts=start_ts)
    except Exception as exc:
        logger.exception("Failed to start recording session")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/session/{session_id}/chunk",
    status_code=status.HTTP_200_OK,
    summary="Upload a live recording stream chunk",
    description="Ingests a time-sliced media chunk from the client browser MediaRecorder stream.",
)
async def upload_chunk(
    session_id: UUID,
    chunk_index: Annotated[int, Form(description="Sequential index of this chunk, starting from 0")],
    chunk: Annotated[UploadFile, File(description="Media stream chunk blob")],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)
    try:
        content = await chunk.read()
        res = service.save_chunk(session_id=session_id, chunk_index=chunk_index, chunk_bytes=content)
        return ok(data=res.model_dump(mode="json"), message="Chunk received.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to upload chunk")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/session/{session_id}/complete",
    status_code=status.HTTP_200_OK,
    summary="Finalize a live lecture recording session",
    description="Stitches received stream chunks, extracts 16kHz mono audio for Whisper STT, generates keyframes, and activates the session.",
)
def complete_session(
    session_id: UUID,
    payload: Optional[SessionCompleteRequest] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)
    try:
        duration = payload.duration_seconds if payload else None
        c_name = payload.course_name_or_code if payload else None
        f_name = payload.faculty_name if payload else None
        classroom = payload.classroom if payload else None
        title = payload.title if payload else None
        notes = payload.notes if payload else None
        res = service.finalize_live_session(
            session_id=session_id,
            duration_seconds=duration,
            course_name_or_code=c_name,
            faculty_name=f_name,
            title=title,
            classroom=classroom,
            notes=notes,
        )
        return ok(data=res.model_dump(mode="json"), message=res.message, start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to finalize session")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a full lecture package (Video/Audio + Slides)",
    description="Batch upload of pre-recorded lecture video, audio, and/or PPTX/PDF presentation slides with metadata.",
)
async def upload_lecture_package(
    course_name_or_code: Annotated[str, Form(description="Course code or name")],
    faculty_name: Annotated[str, Form(description="Instructor name")] = "Faculty",
    title: Annotated[str, Form(description="Lecture title / topic")] = "Lecture Session",
    classroom: Annotated[Optional[str], Form(description="Classroom location")] = None,
    lecture_date: Annotated[Optional[str], Form(description="Date formatted YYYY-MM-DD")] = None,
    video_file: Annotated[Optional[UploadFile], File(description="Lecture video file (MP4, WebM, MKV)")] = None,
    audio_file: Annotated[Optional[UploadFile], File(description="Lecture audio file (WAV, MP3, M4A)")] = None,
    slides_file: Annotated[Optional[UploadFile], File(description="Lecture presentation deck (PPTX, PDF)")] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)

    if not video_file and not audio_file and not slides_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one media file (video, audio, or slides) must be uploaded.",
        )

    parsed_date = None
    if lecture_date:
        try:
            parsed_date = date.fromisoformat(lecture_date.strip())
        except ValueError:
            parsed_date = date.today()

    video_bytes = await video_file.read() if video_file else None
    video_name = video_file.filename if video_file else None

    audio_bytes = await audio_file.read() if audio_file else None
    audio_name = audio_file.filename if audio_file else None

    slides_bytes = await slides_file.read() if slides_file else None
    slides_name = slides_file.filename if slides_file else None

    try:
        res = service.upload_lecture_package(
            course_name_or_code=course_name_or_code,
            faculty_name=faculty_name,
            title=title,
            classroom=classroom,
            lecture_date_val=parsed_date,
            video_filename=video_name,
            video_bytes=video_bytes,
            audio_filename=audio_name,
            audio_bytes=audio_bytes,
            slides_filename=slides_name,
            slides_bytes=slides_bytes,
        )
        return created(data=res.model_dump(mode="json"), message="Lecture package uploaded and processed.", start_ts=start_ts)
    except Exception as exc:
        logger.exception("Lecture package upload failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    summary="List all lecture recording sessions",
    description="Retrieves a paginated list of recorded and uploaded classroom sessions.",
)
def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Annotated[Session, Depends(get_db)] = None,
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)
    res = service.list_sessions(skip=skip, limit=limit)
    return ok(data=res.model_dump(mode="json"), message="Sessions retrieved.", start_ts=start_ts)


@router.get(
    "/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Get detailed lecture session metadata",
    description="Retrieves full technical details, media stream URLs, slide previews, and AI pipeline status for a session.",
)
def get_session(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)
    try:
        res = service.get_session_detail(session_id)
        return ok(data=res.model_dump(mode="json"), message="Session detail retrieved.", start_ts=start_ts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to retrieve session detail")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/handover-contract/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Member 1 Handover Contract for Member 2 (Academic Intelligence)",
    description="Delivers the structured multi-modal lecture handover contract containing transcript segments, visual timelines, presentation slides, and synchronized topic chapters.",
)
def get_handover_contract(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    from app.services.structuring.lecture_structuring_service import LectureStructuringService
    structuring_service = LectureStructuringService(db=db)
    try:
        contract_data = structuring_service.get_structured_lecture(session_id=session_id, db=db)
        return ok(
            data=contract_data.model_dump(mode="json"),
            message="Member 1 Handover Contract retrieved successfully.",
            start_ts=start_ts,
        )
    except Exception as exc:
        logger.exception("Failed to build Handover Contract for session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Handover contract generation failed: {str(exc)}",
        ) from exc


@router.get(
    "/session/{session_id}/export",
    summary="Export complete session package JSON",
    description="Downloads full structured JSON package containing audio transcripts, visual timeline, and multi-track metadata.",
)
def export_session_package(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    from app.services.structuring.lecture_structuring_service import LectureStructuringService
    service = CaptureService(db)
    detail_data = {}
    try:
        detail = service.get_session_detail(session_id)
        detail_data = detail.model_dump(mode="json")
    except Exception:
        detail_data = {"session_id": str(session_id), "status": "ACTIVE"}

    structuring = LectureStructuringService(db=db).get_structured_lecture(session_id=session_id, db=db)

    export_payload = {
        "metadata": detail_data,
        "structuring": structuring.model_dump(mode="json"),
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return JSONResponse(
        content=export_payload,
        headers={"Content-Disposition": f'attachment; filename="lecture_session_{session_id}.json"'},
    )



@router.get(
    "/session/{session_id}/stream",
    summary="Stream video or audio file for a session with Range support",
    description="Streams the raw video or normalized 16kHz audio file directly to media players with HTTP Range request support.",
)
def stream_media(
    session_id: UUID,
    media_type: str = Query("video", pattern="^(video|audio|audio_16k)$"),
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Annotated[Session, Depends(get_db)] = None,
):
    service = CaptureService(db)
    media_path = service.get_media_file_path(session_id, media_type=media_type)
    if not media_path or not media_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found for this session.")

    media_type_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
    }
    content_type = media_type_map.get(media_path.suffix.lower(), "application/octet-stream")
    file_size = media_path.stat().st_size

    if range_header:
        try:
            bytes_unit, byte_range = range_header.strip().split("=")
            if bytes_unit == "bytes":
                start_str, end_str = byte_range.split("-")
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                with open(media_path, "rb") as f:
                    f.seek(start)
                    chunk_data = f.read(length)

                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(length),
                    "Content-Type": content_type,
                }
                return Response(content=chunk_data, status_code=206, headers=headers)
        except Exception as range_err:
            logger.warning("Range parsing fallback: %s", range_err)

    return FileResponse(path=str(media_path), media_type=content_type, filename=media_path.name)


@router.get(
    "/session/{session_id}/slides/{filename}",
    summary="Get slide preview image",
    description="Serves an individual extracted slide preview image.",
)
def get_slide_preview(
    session_id: UUID,
    filename: str,
    db: Annotated[Session, Depends(get_db)],
):
    service = CaptureService(db)
    dirs = service.storage.get_session_paths(session_id)
    slide_file = dirs["slides"] / filename
    if not slide_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slide preview not found.")

    return FileResponse(path=str(slide_file), media_type="image/png", filename=filename)


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a lecture recording session",
    description="Deletes a lecture session and its media recordings from PostgreSQL and purges disk files.",
)
def delete_session(
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    start_ts = time.time()
    service = CaptureService(db)
    deleted = service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return ok(data={"session_id": str(session_id), "deleted": True}, message="Session deleted successfully.", start_ts=start_ts)


