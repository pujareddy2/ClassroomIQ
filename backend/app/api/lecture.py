"""
REST API router for Lecture Intelligence Module.
Versioned under /api/v1/lecture (prefix applied at registration in main.py).

Routes:
  POST /lecture/upload         — Upload lecture audio/video/transcript file or text
  POST /lecture/analyze        — Submit structured transcript JSON
  GET  /lecture/list           — List lectures for a course
  GET  /lecture/{id}           — Get lecture session metadata & transcript info
  GET  /lecture/{id}/status    — Get lecture processing status
  GET  /lecture/{id}/chunks    — Get lecture transcript semantic chunks
  GET  /lecture/{id}/statistics — Get transcript aggregate statistics
  DELETE /lecture/{id}         — Soft-delete lecture session
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timezone
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.lecture_session import LectureSession
from app.models.transcript import Transcript
from app.schemas.response import created, ok
from app.schemas.transcript import (
    ChunkResponse,
    LectureResponse,
    LectureStatisticsResponse,
    LectureStatusResponse,
    TranscriptUploadRequest,
    TranscriptUploadResponse,
)
from app.services.transcript.exceptions import (
    EmptyTranscriptError,
    LectureNotFoundError,
    TranscriptValidationError,
)
from app.services.transcript.transcript_service import TranscriptService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lecture", tags=["Lecture Intelligence"])


@router.get(
    "/list",
    status_code=status.HTTP_200_OK,
    summary="List lectures for a course",
    description="Returns all active lectures for a course or faculty member.",
)
def list_lectures(
    db: Annotated[Session, Depends(get_db)],
    course_id: str | None = Query(None),
) -> dict:
    try:
        query = db.query(LectureSession).filter(LectureSession.deleted_at.is_(None))

        if course_id and course_id.strip():
            try:
                val_uuid = UUID(course_id.strip())
                query = query.filter(LectureSession.course_id == val_uuid)
            except ValueError:
                course = db.query(Course).filter(
                    (Course.course_code.ilike(course_id.strip())) | (Course.course_name.ilike(course_id.strip()))
                ).first()
                if course:
                    query = query.filter(LectureSession.course_id == course.id)

        lectures = query.order_by(LectureSession.created_at.desc()).all()

        items = []
        for l in lectures:
            transcript = db.query(Transcript).filter(Transcript.lecture_id == l.id).first()
            has_transcript = transcript is not None

            status_str = "READY" if has_transcript else "PROCESSING"

            f_name = "Faculty"
            if l.faculty and hasattr(l.faculty, "user") and l.faculty.user:
                f_name = str(l.faculty.user.full_name)

            c_name = "Course"
            if l.course and hasattr(l.course, "course_name"):
                c_name = str(l.course.course_name)

            items.append({
                "id": str(l.id),
                "lecture_id": str(l.id),
                "title": str(l.title or c_name or "Class Lecture Session"),
                "course_id": str(l.course_id),
                "course_name": c_name,
                "faculty_id": str(l.faculty_id),
                "faculty_name": f_name,
                "lecture_date": str(l.lecture_date) if l.lecture_date else date.today().isoformat(),
                "duration_minutes": l.duration_minutes or 45,
                "classroom": str(l.classroom or "Main Lecture Hall"),
                "has_transcript": has_transcript,
                "transcript_id": str(transcript.id) if transcript else None,
                "total_words": transcript.total_words if transcript else 0,
                "status": status_str,
                "created_at": str(l.created_at) if l.created_at else None,
            })

        return ok(data=items, message="Lectures retrieved successfully.")
    except Exception as exc:
        logger.exception("Error in list_lectures")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload lecture recording or transcript file",
    description="Uploads a lecture transcript file (.txt, .pdf, .json, .docx) or text content, processes chunks & curriculum mappings.",
)
async def upload_lecture(
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str, Form(...)],
    course_id: Annotated[str, Form(...)],
    faculty_name: Annotated[str | None, Form(...)] = "Faculty Member",
    lecture_date: Annotated[str | None, Form(...)] = None,
    file: Annotated[UploadFile | None, File(...)] = None,
    raw_text: Annotated[str | None, Form(...)] = None,
) -> dict:
    start_ts = time.time()

    # 1. Resolve Course
    course = None
    try:
        c_uuid = UUID(course_id.strip())
        course = db.get(Course, c_uuid)
    except ValueError:
        pass

    if not course:
        course = db.query(Course).filter(
            (Course.course_code.ilike(course_id.strip())) | (Course.course_name.ilike(course_id.strip()))
        ).first()

    if not course:
        course = db.query(Course).first()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No course found to associate lecture with.")

    # 2. Resolve Faculty
    faculty = db.query(Faculty).join(Faculty.user).filter(
        Faculty.user.has(full_name=faculty_name.strip())
    ).first() if faculty_name else None

    if not faculty:
        faculty = db.query(Faculty).first()
        if not faculty:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No faculty record found.")

    # 3. Read content
    transcript_text = ""
    if file:
        content_bytes = await file.read()
        filename = (file.filename or "").lower()
        if filename.endswith(".json"):
            try:
                parsed_json = json.loads(content_bytes.decode("utf-8", errors="ignore").replace("\x00", ""))
                if isinstance(parsed_json, list):
                    transcript_items = parsed_json
                elif isinstance(parsed_json, dict) and "transcript" in parsed_json:
                    transcript_items = parsed_json["transcript"]
                else:
                    transcript_items = [{"speaker": "Faculty", "start": 0.0, "end": 60.0, "text": str(parsed_json).replace("\x00", "")}]
            except Exception:
                transcript_text = content_bytes.decode("utf-8", errors="ignore").replace("\x00", "")
                transcript_items = None
        else:
            transcript_text = content_bytes.decode("utf-8", errors="ignore").replace("\x00", "")
            transcript_items = None
    elif raw_text and raw_text.strip():
        transcript_text = raw_text.strip().replace("\x00", "")
        transcript_items = None
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a lecture file or provide transcript text.")

    # Format transcript items if text
    if not transcript_items:
        lines = [line.strip().replace("\x00", "") for line in transcript_text.splitlines() if line.strip()]
        if not lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file contains no readable transcript text.")
        
        transcript_items = []
        current_time = 0.0
        for idx, line in enumerate(lines):
            dur = max(3.0, len(line.split()) * 0.4)
            speaker = "Faculty"
            text_val = line
            if ":" in line and len(line.split(":")[0]) < 20:
                parts = line.split(":", 1)
                speaker = parts[0].strip().replace("\x00", "")
                text_val = parts[1].strip().replace("\x00", "")

            transcript_items.append({
                "speaker": speaker,
                "start": round(current_time, 2),
                "end": round(current_time + dur, 2),
                "text": text_val,
            })
            current_time += dur

    # 4. Create Lecture Session
    parsed_date = date.today()
    if lecture_date:
        try:
            parsed_date = date.fromisoformat(lecture_date.strip())
        except ValueError:
            pass

    lecture = LectureSession(
        course_id=course.id,
        faculty_id=faculty.id,
        title=title.strip(),
        lecture_date=parsed_date,
        duration_minutes=max(15, int(transcript_items[-1]["end"] // 60)),
        classroom="Lecture Hall A",
    )
    db.add(lecture)
    db.flush()

    # 5. Process & Store Transcript through TranscriptService
    service = TranscriptService(db)
    result = service.process_and_store_transcript(
        lecture_id=lecture.id,
        course_name_or_code=course.course_name,
        faculty_name=faculty.user.full_name if faculty.user else "Faculty",
        transcript_data=transcript_items,
        lecture_date=parsed_date,
    )
    db.commit()

    response_data = {
        "id": str(lecture.id),
        "lecture_id": str(lecture.id),
        "title": lecture.title,
        "course_id": str(course.id),
        "course_name": course.course_name,
        "duration_minutes": lecture.duration_minutes,
        "status": "READY",
        "result": result,
    }

    return created(data=response_data, message="Lecture uploaded, processed, and transcribed successfully.", start_ts=start_ts)


@router.post(
    "/analyze",
    status_code=status.HTTP_201_CREATED,
    summary="Submit structured transcript JSON",
    description="Accepts structured diarized transcript payload and processes curriculum mapping.",
)
def analyze_transcript(
    payload: TranscriptUploadRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        start = time.time()
        transcript_items = [t.model_dump() for t in payload.transcript]
        result = service.process_and_store_transcript(
            lecture_id=payload.lecture_id,
            course_name_or_code=payload.course_id or "Unknown Course",
            faculty_name=payload.faculty_name or "Faculty",
            transcript_data=transcript_items,
            curriculum_id=payload.curriculum_id,
        )
        db.commit()
        return created(
            data=TranscriptUploadResponse(**result).model_dump(),
            message="Transcript processed and stored successfully.",
            start_ts=start,
        )
    except EmptyTranscriptError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TranscriptValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error processing transcript")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}",
    status_code=status.HTTP_200_OK,
    summary="Get lecture session metadata",
)
def get_lecture(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        start = time.time()
        lecture = db.get(LectureSession, lecture_id)
        if not lecture or lecture.deleted_at is not None:
            raise LectureNotFoundError(f"Lecture '{lecture_id}' not found")

        transcript = db.query(Transcript).filter(Transcript.lecture_id == lecture_id).first()
        data = {
            "id": str(lecture.id),
            "lecture_id": str(lecture.id),
            "title": lecture.title or (lecture.course.course_name if lecture.course else "Lecture Session"),
            "course_id": str(lecture.course_id),
            "course_name": lecture.course.course_name if lecture.course else "Course",
            "faculty_id": str(lecture.faculty_id),
            "faculty_name": lecture.faculty.user.full_name if lecture.faculty and lecture.faculty.user else "Faculty",
            "lecture_date": str(lecture.lecture_date),
            "duration_minutes": lecture.duration_minutes,
            "classroom": lecture.classroom,
            "has_transcript": transcript is not None,
            "transcript_id": str(transcript.id) if transcript else None,
            "total_words": transcript.total_words if transcript else 0,
            "raw_text": transcript.raw_text if transcript else None,
            "cleaned_text": transcript.cleaned_text if transcript else None,
            "status": "READY" if transcript else "PROCESSING",
            "created_at": lecture.created_at.isoformat() if lecture.created_at else None,
        }
        return ok(data=data, message="Lecture metadata retrieved.", start_ts=start)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching lecture")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Get lecture processing pipeline status",
)
def get_lecture_status(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        start = time.time()
        data = service.get_lecture_status(lecture_id)
        return ok(data=data, message="Lecture processing status retrieved.", start_ts=start)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching lecture status")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/chunks",
    status_code=status.HTTP_200_OK,
    summary="Get semantic transcript chunks for lecture",
)
def get_lecture_chunks(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        start = time.time()
        chunks = service.get_lecture_chunks(lecture_id)
        return ok(data=chunks, message="Lecture chunks retrieved.", start_ts=start)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching chunks")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{lecture_id}/statistics",
    status_code=status.HTTP_200_OK,
    summary="Get lecture transcript processing statistics",
)
def get_lecture_statistics(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        start = time.time()
        stats = service.get_lecture_statistics(lecture_id)
        return ok(data=stats, message="Lecture statistics retrieved.", start_ts=start)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching statistics")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post(
    "/upload-transcript",
    status_code=status.HTTP_201_CREATED,
    summary="Upload transcript JSON (legacy endpoint)",
)
def upload_transcript(
    payload: TranscriptUploadRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return analyze_transcript(payload, db)


@router.get(
    "/{lecture_id}/mappings",
    status_code=status.HTTP_200_OK,
    summary="Get transcript-to-curriculum mappings",
)
def get_lecture_mappings(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = TranscriptService(db)
    try:
        start = time.time()
        mappings = service.get_lecture_mappings(lecture_id)
        return ok(data=mappings, message="Lecture topic mappings retrieved.", start_ts=start)
    except LectureNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error fetching mappings")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.delete(
    "/{lecture_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete lecture session",
)
def delete_lecture(
    lecture_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    lecture = db.get(LectureSession, lecture_id)
    if not lecture or lecture.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found.")

    lecture.deleted_at = datetime.now(timezone.utc)
    lecture.status = "DELETED"
    db.commit()

    return ok(data={"id": str(lecture_id)}, message="Lecture session deleted successfully.")
