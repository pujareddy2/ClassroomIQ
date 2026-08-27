"""
Lecture Capture & Multimedia Service.
Orchestrates live recording sessions, chunk ingestion, file uploads,
FFmpeg audio/video processing, slide deck extraction, and database persistence.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.institution import Institution
from app.models.lecture_session import LectureSession
from app.models.recording import Recording
from app.models.user import User
from app.schemas.multimedia import (
    ChunkUploadResponse,
    LectureUploadResponse,
    MediaMetadataResponse,
    SessionCompleteResponse,
    SessionDetailResponse,
    SessionInitResponse,
    SessionListResponse,
    SessionSummaryResponse,
    SlideItemResponse,
    SlideSummaryResponse,
)
from app.services.multimedia.ffmpeg_processor import FFmpegProcessor
from app.services.multimedia.slide_processor import SlideProcessor
from app.services.multimedia.storage_service import MultimediaStorageService

logger = logging.getLogger(__name__)


class CaptureService:
    """Manages classroom lecture capture, uploads, and media extraction."""

    def __init__(self, db: Session, storage_service: Optional[MultimediaStorageService] = None):
        self.db = db
        self.storage = storage_service or MultimediaStorageService()
        self.ffmpeg = FFmpegProcessor()
        self.slides = SlideProcessor()

    def _resolve_course_and_faculty(
        self,
        course_name_or_code: str,
        faculty_name: str,
    ) -> tuple[Course, Faculty]:
        """Resolves exact course/faculty specified by user or creates new records seamlessly."""
        # 1. Resolve Faculty
        clean_fac_name = (faculty_name or "Faculty").strip()
        faculty = self.db.query(Faculty).join(Faculty.user).filter(
            Faculty.user.has(User.full_name.ilike(clean_fac_name))
        ).first()

        if not faculty:
            user = self.db.query(User).filter(User.full_name.ilike(clean_fac_name)).first()
            if not user:
                safe_email = f"faculty_{uuid.uuid4().hex[:6]}@classroomiq.ai"
                user = User(
                    email=safe_email,
                    full_name=clean_fac_name,
                    password_hash="dev_placeholder",
                    role="FACULTY",
                )
                self.db.add(user)
                self.db.flush()

            inst = self.db.query(Institution).first()
            if not inst:
                inst = Institution(name="University", contact_email="admin@classroomiq.ai")
                self.db.add(inst)
                self.db.flush()

            dept = self.db.query(Department).first()
            if not dept:
                dept = Department(institution_id=inst.id, name="General Academics", code="GEN")
                self.db.add(dept)
                self.db.flush()

            faculty = Faculty(
                user_id=user.id,
                department_id=dept.id,
                employee_id=f"FAC_{uuid.uuid4().hex[:6].upper()}",
                designation="Faculty Member",
            )
            self.db.add(faculty)
            self.db.flush()

        # 2. Resolve Course
        clean_course = (course_name_or_code or "CS101 - General Course").strip()
        if " - " in clean_course:
            parts = clean_course.split(" - ", 1)
            code = parts[0].strip().upper()
            name = parts[1].strip()
        else:
            code = clean_course[:20].strip().upper()
            name = clean_course.strip()

        # Look up by code or name
        course = self.db.query(Course).filter(
            (Course.course_code.ilike(code)) |
            (Course.course_code.ilike(clean_course)) |
            (Course.course_name.ilike(name)) |
            (Course.course_name.ilike(clean_course))
        ).first()

        if course:
            # If course already exists with this code, update name if user gave new title
            if name and name != code and course.course_name != name:
                course.course_name = name
                self.db.flush()
        else:
            course = Course(
                department_id=faculty.department_id,
                course_code=code[:20].upper(),
                course_name=name or code,
                credits=3,
            )
            self.db.add(course)
            self.db.flush()

        return course, faculty

    def init_live_session(
        self,
        course_name_or_code: str = "General Lecture",
        faculty_name: str = "Faculty",
        title: str = "Classroom Lecture",
        classroom: Optional[str] = "Classroom 101",
        consent_confirmed: bool = True,
        has_screen_share: bool = False,
    ) -> SessionInitResponse:
        """Initializes a new live classroom recording session in DB and on disk."""
        course, faculty = self._resolve_course_and_faculty(course_name_or_code, faculty_name)

        lecture = LectureSession(
            course_id=course.id,
            faculty_id=faculty.id,
            lecture_date=date.today(),
            duration_minutes=0,
            classroom=classroom or "Virtual / Recorded",
            status="RECORDING",
        )
        self.db.add(lecture)
        self.db.flush()

        recording = Recording(
            session_id=lecture.id,
            status="RECORDING",
        )
        self.db.add(recording)
        self.db.flush()

        # Initialize session storage directories on disk
        dirs = self.storage.init_session_dir(lecture.id)
        self.db.commit()

        logger.info(
            "Initialized live session %s for course '%s' (faculty: '%s', classroom: '%s')",
            lecture.id,
            course.course_name,
            faculty.user.full_name if faculty.user else "Faculty",
            classroom,
        )

        return SessionInitResponse(
            session_id=lecture.id,
            recording_id=recording.id,
            status="RECORDING",
            started_at=datetime.now(timezone.utc),
            upload_chunk_url=f"/api/v1/multimedia/session/{lecture.id}/chunk",
            complete_session_url=f"/api/v1/multimedia/session/{lecture.id}/complete",
        )

    def append_live_chunk(
        self,
        session_id: UUID,
        chunk_index: int,
        chunk_bytes: bytes,
    ) -> ChunkUploadResponse:
        """Saves an incoming WebM/H.264 video chunk to session disk storage."""
        lecture = self.db.get(LectureSession, session_id)
        if not lecture:
            raise ValueError(f"Lecture session {session_id} not found")

        file_path, bytes_written = self.storage.save_chunk(session_id, chunk_index, chunk_bytes)
        total_chunks = self.storage.get_chunks_count(session_id)

        return ChunkUploadResponse(
            session_id=session_id,
            chunk_index=chunk_index,
            bytes_written=bytes_written,
            total_chunks=total_chunks,
            status="CHUNK_RECEIVED",
        )

    # Alias for API compatibility
    save_chunk = append_live_chunk

    def finalize_live_session(
        self,
        session_id: UUID,
        duration_seconds: Optional[float] = None,
        course_name_or_code: Optional[str] = None,
        faculty_name: Optional[str] = None,
        title: Optional[str] = None,
        classroom: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> SessionCompleteResponse:
        """Assembles stream chunks, extracts 16kHz WAV, updates session metadata, and marks session ACTIVE."""
        lecture = self.db.get(LectureSession, session_id)
        if not lecture:
            raise ValueError(f"Lecture session {session_id} not found")

        # Update metadata if user updated details during session
        if course_name_or_code or faculty_name:
            c_name = course_name_or_code or (lecture.course.course_name if lecture.course else "General Lecture")
            f_name = faculty_name or (lecture.faculty.user.full_name if (lecture.faculty and lecture.faculty.user) else "Faculty")
            course, faculty = self._resolve_course_and_faculty(c_name, f_name)
            lecture.course_id = course.id
            lecture.faculty_id = faculty.id

        if classroom:
            lecture.classroom = classroom

        recording = self.db.query(Recording).filter(Recording.session_id == session_id).first()
        if not recording:
            recording = Recording(session_id=session_id)
            self.db.add(recording)

        dirs = self.storage.init_session_dir(session_id)

        # 1. Assemble raw video
        try:
            raw_video = self.storage.assemble_chunks(session_id, output_filename="recorded_lecture.webm")
            recording.video_path = str(raw_video)
        except Exception as exc:
            logger.warning("Chunk assembly warning for session %s: %s", session_id, exc)
            raw_video = None

        # 2. Extract 16kHz mono audio for Whisper STT
        audio_16k_path = dirs["audio"] / "audio_16k.wav"
        if raw_video and raw_video.exists():
            self.ffmpeg.extract_audio_16k_mono(raw_video, audio_16k_path)
            recording.audio_path = str(audio_16k_path)
            # Extract keyframe thumbnails
            self.ffmpeg.extract_video_keyframes(raw_video, dirs["frames"], interval_seconds=30.0)

        # 3. Calculate duration
        computed_duration = duration_seconds
        if raw_video and raw_video.exists() and not computed_duration:
            meta = self.ffmpeg.probe_media(raw_video)
            computed_duration = meta.get("duration_seconds")

        if computed_duration:
            lecture.duration_minutes = max(1, int(computed_duration // 60))

        lecture.status = "ACTIVE"
        recording.status = "ACTIVE"
        self.db.commit()

        slide_count = len(self.storage.list_slide_frames(session_id))

        logger.info("Finalized live session %s (duration: %s s)", session_id, computed_duration)

        return SessionCompleteResponse(
            session_id=session_id,
            recording_id=recording.id,
            status="ACTIVE",
            video_path=recording.video_path,
            audio_path=recording.audio_path,
            audio_16k_path=str(audio_16k_path) if audio_16k_path.exists() else None,
            duration_seconds=computed_duration,
            slide_count=slide_count,
            message="Live lecture recording finalized and queued for AI intelligence pipeline.",
        )

    def upload_lecture_package(
        self,
        course_name_or_code: str,
        faculty_name: str,
        title: str,
        classroom: Optional[str] = None,
        lecture_date_val: Optional[date] = None,
        video_filename: Optional[str] = None,
        video_bytes: Optional[bytes] = None,
        audio_filename: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        slides_filename: Optional[str] = None,
        slides_bytes: Optional[bytes] = None,
    ) -> LectureUploadResponse:
        """Handles full upload of a pre-recorded lecture (video, audio, and/or slide presentation)."""
        course, faculty = self._resolve_course_and_faculty(course_name_or_code, faculty_name)

        session_id = uuid.uuid4()
        dirs = self.storage.init_session_dir(session_id)

        saved_video_path: Optional[Path] = None
        saved_audio_path: Optional[Path] = None
        saved_slides_path: Optional[Path] = None
        slide_count = 0

        # Save video
        if video_filename and video_bytes:
            saved_video_path = self.storage.save_raw_file(session_id, video_filename, video_bytes, category="raw")

        # Save audio
        if audio_filename and audio_bytes:
            saved_audio_path = self.storage.save_raw_file(session_id, audio_filename, audio_bytes, category="audio")

        # Save & process slides
        if slides_filename and slides_bytes:
            saved_slides_path = self.storage.save_raw_file(session_id, slides_filename, slides_bytes, category="slides")
            slides_data = self.slides.process_presentation(saved_slides_path, dirs["slides"])
            slide_count = len(slides_data)

        # Ensure we have 16kHz mono audio for downstream Whisper STT
        audio_16k_path = dirs["audio"] / "audio_16k.wav"
        media_source = saved_video_path or saved_audio_path
        has_extracted_audio = False

        duration_minutes = 60
        if media_source and media_source.exists():
            self.ffmpeg.extract_audio_16k_mono(media_source, audio_16k_path)
            has_extracted_audio = audio_16k_path.exists()

            # Probe media metadata for duration
            meta = self.ffmpeg.probe_media(media_source)
            if meta.get("duration_seconds"):
                duration_minutes = max(1, int(meta["duration_seconds"] // 60))

            # Extract video keyframes if video was uploaded
            if saved_video_path and saved_video_path.exists():
                self.ffmpeg.extract_video_keyframes(saved_video_path, dirs["frames"])

        # Persist DB records
        lecture = LectureSession(
            id=session_id,
            course_id=course.id,
            faculty_id=faculty.id,
            lecture_date=lecture_date_val or date.today(),
            duration_minutes=duration_minutes,
            classroom=classroom or "Virtual Classroom",
            status="ACTIVE",
        )
        self.db.add(lecture)
        self.db.flush()

        recording = Recording(
            session_id=session_id,
            video_path=str(saved_video_path) if saved_video_path else None,
            audio_path=str(audio_16k_path if has_extracted_audio else (saved_audio_path or "")),
            status="ACTIVE",
        )
        self.db.add(recording)
        self.db.commit()

        logger.info("Uploaded lecture package for session %s (course: %s, slides: %d)", session_id, course.course_code, slide_count)

        return LectureUploadResponse(
            session_id=session_id,
            recording_id=recording.id,
            title=title or course.course_name,
            course_name=course.course_name,
            faculty_name=faculty.user.full_name if faculty.user else faculty_name,
            video_filename=video_filename,
            audio_filename=audio_filename,
            slides_filename=slides_filename,
            has_extracted_audio=has_extracted_audio,
            slide_count=slide_count,
            status="ACTIVE",
            created_at=datetime.now(timezone.utc),
        )

    def get_session_detail(self, session_id: UUID) -> SessionDetailResponse:
        """Retrieves comprehensive session detail including media links and slide items."""
        lecture = self.db.get(LectureSession, session_id)
        if not lecture:
            raise ValueError(f"Lecture session {session_id} not found")

        recording = self.db.query(Recording).filter(Recording.session_id == session_id).first()
        dirs = self.storage.get_session_paths(session_id)

        # Check media paths
        video_url = f"/api/v1/multimedia/session/{session_id}/stream?media_type=video" if (recording and recording.video_path) else None
        audio_url = f"/api/v1/multimedia/session/{session_id}/stream?media_type=audio" if (recording and recording.audio_path) else None
        audio_16k_file = dirs["audio"] / "audio_16k.wav"
        audio_16k_url = f"/api/v1/multimedia/session/{session_id}/stream?media_type=audio_16k" if audio_16k_file.exists() else None

        # Slides metadata
        slides_files = sorted(dirs["slides"].glob("slide_*.png") or dirs["slides"].glob("slide_*.jpg"))
        slide_items: List[SlideItemResponse] = []
        for idx, slide_path in enumerate(slides_files, start=1):
            slide_items.append(SlideItemResponse(
                slide_number=idx,
                title=f"Slide {idx}",
                text_content="",
                preview_url=f"/api/v1/multimedia/session/{session_id}/slides/{slide_path.name}",
            ))

        # Media probe
        media_meta: Optional[MediaMetadataResponse] = None
        target_file = Path(recording.video_path) if (recording and recording.video_path) else (audio_16k_file if audio_16k_file.exists() else None)
        if target_file and target_file.exists():
            meta = self.ffmpeg.probe_media(target_file)
            media_meta = MediaMetadataResponse(**meta)

        # Check downstream flags
        has_transcript = bool(recording and getattr(recording, 'transcript', None))
        has_coverage = bool(getattr(lecture, 'coverage_report', None) or getattr(lecture, 'reports', None))
        has_validation = bool(getattr(lecture, 'recommendations', None))

        return SessionDetailResponse(
            session_id=session_id,
            recording_id=recording.id if recording else None,
            title=f"{lecture.course.course_name} — Lecture" if lecture.course else "Classroom Lecture",
            course_name=lecture.course.course_name if lecture.course else "Unknown Course",
            faculty_name=lecture.faculty.user.full_name if (lecture.faculty and lecture.faculty.user) else "Faculty",
            classroom=lecture.classroom,
            status=lecture.status,
            created_at=lecture.created_at,
            updated_at=lecture.updated_at,
            duration_seconds=float(lecture.duration_minutes * 60) if lecture.duration_minutes else None,
            video_url=video_url,
            audio_url=audio_url,
            audio_16k_url=audio_16k_url,
            slides_url=f"/api/v1/multimedia/session/{session_id}/slides" if slide_items else None,
            slide_count=len(slide_items),
            slides=slide_items,
            media_metadata=media_meta,
            has_transcript=has_transcript,
            has_coverage=has_coverage,
            has_validation=has_validation,
        )

    def list_sessions(self, skip: int = 0, limit: int = 50) -> SessionListResponse:
        """Lists all lecture recording sessions."""
        total = self.db.query(LectureSession).count()
        lectures = self.db.query(LectureSession).order_by(LectureSession.created_at.desc()).offset(skip).limit(limit).all()

        items: List[SessionSummaryResponse] = []
        for lec in lectures:
            rec = lec.recording
            dirs = self.storage.get_session_paths(lec.id)
            slide_count = len(list(dirs["slides"].glob("slide_*.*")))

            items.append(SessionSummaryResponse(
                session_id=lec.id,
                recording_id=rec.id if rec else None,
                title=f"{lec.course.course_name} — Lecture" if lec.course else "Lecture",
                course_name=lec.course.course_name if lec.course else "Unknown Course",
                faculty_name=lec.faculty.user.full_name if (lec.faculty and lec.faculty.user) else "Faculty",
                classroom=lec.classroom,
                status=lec.status,
                created_at=lec.created_at,
                duration_seconds=float(lec.duration_minutes * 60) if lec.duration_minutes else None,
                has_video=bool(rec and rec.video_path),
                has_audio=bool(rec and rec.audio_path),
                has_slides=slide_count > 0,
                slide_count=slide_count,
            ))

        return SessionListResponse(total=total, items=items)

    def get_media_file_path(self, session_id: UUID, media_type: str = "video") -> Optional[Path]:
        """Resolves the physical disk path for streaming a session media file."""
        dirs = self.storage.get_session_paths(session_id)
        if media_type == "video":
            rec = self.db.query(Recording).filter(Recording.session_id == session_id).first()
            if rec and rec.video_path and Path(rec.video_path).exists():
                return Path(rec.video_path)
            # Check raw directory
            raw_files = list(dirs["raw"].glob("*.webm")) + list(dirs["raw"].glob("*.mp4"))
            return raw_files[0] if raw_files else None
        elif media_type in {"audio_16k", "audio"}:
            audio_16k = dirs["audio"] / "audio_16k.wav"
            if audio_16k.exists():
                return audio_16k
            rec = self.db.query(Recording).filter(Recording.session_id == session_id).first()
            if rec and rec.audio_path and Path(rec.audio_path).exists():
                return Path(rec.audio_path)
        return None

    def delete_session(self, session_id: UUID) -> bool:
        """Deletes a lecture session and its recording from PostgreSQL and purges disk files."""
        lecture = self.db.get(LectureSession, session_id)
        if not lecture:
            return False

        # Delete database records
        self.db.delete(lecture)
        self.db.commit()

        # Purge files from disk
        self.storage.delete_session_dir(session_id)
        logger.info("Purged session %s from database and disk", session_id)
        return True

