"""
Main Audio Intelligence Orchestrator.
Coordinates VAD, Whisper STT, Diarization, PostgreSQL persistence, and Academic Intelligence sync.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lecture_session import LectureSession
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.transcript_segment import TranscriptSegment
from app.schemas.audio import (
    AudioProcessResponse,
    AudioTranscriptResponse,
    DiarizationSummary,
    DiarizedSegmentItem,
    TranscriptSyncResponse,
)
from app.services.audio.diarization_engine import DiarizationEngine
from app.services.audio.vad_service import VADService
from app.services.audio.whisper_engine import WhisperEngine
from app.services.multimedia.storage_service import MultimediaStorageService
from app.services.transcript.transcript_cleaner import TranscriptCleaner
from app.services.transcript.transcript_service import TranscriptService

logger = logging.getLogger(__name__)


class AudioIntelligenceService:
    """End-to-end Audio Intelligence pipeline: VAD -> Whisper STT -> Diarization -> Academic Sync."""

    def __init__(self, db: Session, storage_service: Optional[MultimediaStorageService] = None):
        self.db = db
        self.storage = storage_service or MultimediaStorageService()
        self.vad = VADService()
        self.whisper = WhisperEngine()
        self.diarization = DiarizationEngine()

    def process_session_audio(
        self,
        session_id: UUID,
        domain_subject: Optional[str] = "auto",
        domain_vocabulary: Optional[List[str]] = None,
        language: Optional[str] = "auto",
        model_size: Optional[str] = "base",
        diarization_mode: Optional[str] = "lecture",
        boost_audio_volume: bool = True,
        enable_vad: bool = True,
        enable_diarization: bool = True,
        sync_academic: bool = True,
    ) -> AudioProcessResponse:
        """Executes adaptable speech-to-text and diarization pipeline for any audio/video recording."""
        start_time = time.perf_counter()

        dirs = self.storage.get_session_paths(session_id)
        session_dir = self.storage.get_session_dir(session_id)
        target_16k_wav = dirs["audio"] / "audio_16k.wav"

        # 1. Locate source recording file (audio or video)
        source_media: Optional[Path] = None
        if self.db:
            rec = self.db.query(Recording).filter(Recording.session_id == session_id).first()
            if rec and rec.audio_path and Path(rec.audio_path).exists():
                source_media = Path(rec.audio_path)
            elif rec and rec.video_path and Path(rec.video_path).exists():
                source_media = Path(rec.video_path)

        if not source_media or not source_media.exists():
            candidates = (
                list(dirs["audio"].glob("*.wav"))
                + list(dirs["raw"].glob("*.wav"))
                + list(dirs["raw"].glob("*.webm"))
                + list(dirs["raw"].glob("*.mp4"))
                + list(session_dir.glob("**/*.wav"))
                + list(session_dir.glob("**/*.webm"))
                + list(session_dir.glob("**/*.mp4"))
            )
            # Exclude target file itself from candidates if already exists
            filtered = [c for c in candidates if c.resolve() != target_16k_wav.resolve()]
            if filtered:
                source_media = filtered[0]
            elif target_16k_wav.exists():
                source_media = target_16k_wav

        if not source_media or not source_media.exists():
            raise FileNotFoundError(f"No audio file found for session {session_id}. Please upload or record media first.")

        # 2. Ensure pristine 16kHz Mono WAV conversion via FFmpeg Processor
        if not target_16k_wav.exists() or target_16k_wav.stat().st_size == 0 or source_media.suffix.lower() != ".wav":
            try:
                from app.services.multimedia.ffmpeg_processor import FFmpegProcessor
                ffmpeg = FFmpegProcessor()
                target_16k_wav.parent.mkdir(parents=True, exist_ok=True)
                ffmpeg.extract_audio_16k_mono(source_media, target_16k_wav)
            except Exception as ffmpeg_err:
                logger.warning("FFmpeg 16k extraction warning: %s; using source media directly", ffmpeg_err)

        audio_file = target_16k_wav if (target_16k_wav.exists() and target_16k_wav.stat().st_size > 0) else source_media

        # 1. Voice Activity Detection (VAD)
        vad_segments = []

        if enable_vad:
            vad_segments = self.vad.detect_speech_intervals(audio_file)

        # 2. Whisper Speech-to-Text Transcription with domain and language adaptation
        raw_transcription = self.whisper.transcribe_audio(
            audio_path=audio_file,
            domain_subject=domain_subject,
            domain_vocabulary=domain_vocabulary,
            language=language,
            model_size=model_size,
        )

        # 3. Speaker Diarization (Acoustic Spectral Clustering & Turn Attribution)
        if enable_diarization:
            diarized_segments, diarization_summary = self.diarization.diarize_segments(
                raw_segments=raw_transcription,
                audio_path=audio_file,
                diarization_mode=diarization_mode or "lecture",
            )
        else:
            diarized_segments, diarization_summary = self.diarization.diarize_segments(
                raw_segments=raw_transcription,
                audio_path=audio_file,
                diarization_mode="solo",
                primary_speaker_label="Speaker",
            )

        # 4. PostgreSQL Persistence & Disk Caching
        transcript_id = session_id
        if self.db:
            try:
                transcript = self.db.query(Transcript).filter(Transcript.lecture_id == session_id).first()
                if not transcript:
                    rec = self.db.query(Recording).filter(Recording.session_id == session_id).first()
                    transcript = Transcript(
                        lecture_id=session_id,
                        recording_id=rec.id if rec else None,
                        language=language or "en",
                    )
                    self.db.add(transcript)
                    self.db.flush()

                transcript_id = transcript.id
                raw_text_pieces = [f"{s.speaker}: {s.text}" for s in diarized_segments]
                raw_full_text = "\n".join(raw_text_pieces)
                cleaned_text = TranscriptCleaner.clean_text(raw_full_text)

                transcript.total_words = diarization_summary.total_words
                transcript.raw_text = raw_full_text
                transcript.cleaned_text = cleaned_text
                self.db.flush()

                # Remove previous segments if re-processing
                self.db.query(TranscriptSegment).filter(TranscriptSegment.transcript_id == transcript.id).delete()
                self.db.flush()

                # Insert new diarized segments
                for seg in diarized_segments:
                    ts_seg = TranscriptSegment(
                        transcript_id=transcript.id,
                        speaker=seg.speaker,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        transcript_text=seg.text,
                    )
                    self.db.add(ts_seg)
                    self.db.flush()
                    seg.segment_id = ts_seg.id

                self.db.commit()
            except Exception as db_err:
                self.db.rollback()
                logger.warning("DB transcript storage non-critical warning: %s", db_err)

        # Also cache transcript to disk
        try:
            session_dir = self.storage.get_session_dir(session_id)
            import json
            cache_payload = {
                "session_id": str(session_id),
                "has_transcript": True,
                "language": language or "en",
                "total_words": diarization_summary.total_words,
                "diarization_summary": diarization_summary.model_dump(mode="json"),
                "segments": [s.model_dump(mode="json") for s in diarized_segments],
            }
            (session_dir / "transcript.json").write_text(json.dumps(cache_payload, indent=2), encoding="utf-8")
        except Exception as disk_err:
            logger.warning("Could not persist transcript.json: %s", disk_err)

        # 5. Sync with Member 2 Academic Intelligence
        academic_synced = False
        academic_summary = None
        if sync_academic and diarized_segments and self.db:
            try:
                lecture = self.db.get(LectureSession, session_id)
                course_title = lecture.course.course_name if (lecture and lecture.course) else "General Lecture"
                fac_name = lecture.faculty.user.full_name if (lecture and lecture.faculty and lecture.faculty.user) else "Faculty"

                academic_service = TranscriptService(self.db)
                transcript_items = [
                    {"speaker": s.speaker, "start": s.start_time, "end": s.end_time, "text": s.text}
                    for s in diarized_segments
                ]
                academic_res = academic_service.process_and_store_transcript(
                    lecture_id=session_id,
                    course_name_or_code=course_title,
                    faculty_name=fac_name,
                    transcript_data=transcript_items,
                )
                self.db.commit()
                academic_synced = True
                academic_summary = academic_res
                logger.info("Academic Intelligence sync successful for session %s", session_id)
            except Exception as academic_err:
                if self.db:
                    self.db.rollback()
                logger.warning("Academic sync non-critical warning: %s", academic_err)


        elapsed = round(time.perf_counter() - start_time, 2)

        return AudioProcessResponse(
            session_id=session_id,
            transcript_id=transcript_id,
            status="COMPLETED",
            language="en",
            total_words=diarization_summary.total_words,
            total_segments=len(diarized_segments),
            duration_seconds=diarization_summary.teacher_speaking_time_sec + diarization_summary.student_speaking_time_sec,
            diarization_summary=diarization_summary,
            segments=diarized_segments,
            academic_synced=academic_synced,
            academic_summary=academic_summary,
            processing_time_sec=elapsed,
        )

    def get_session_transcript(self, session_id: UUID) -> AudioTranscriptResponse:
        """Retrieves structured diarized transcript for a session."""
        transcript = self.db.query(Transcript).filter(Transcript.lecture_id == session_id).first() if self.db else None
        if not transcript:
            # Check disk cache
            session_dir = self.storage.get_session_dir(session_id)
            cache_file = session_dir / "transcript.json"
            if cache_file.exists():
                try:
                    import json
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    return AudioTranscriptResponse.model_validate(data)
                except Exception as err:
                    logger.warning("Failed to load transcript.json for %s: %s", session_id, err)

            return AudioTranscriptResponse(
                session_id=session_id,
                has_transcript=False,
            )


        db_segments = (
            self.db.query(TranscriptSegment)
            .filter(TranscriptSegment.transcript_id == transcript.id)
            .order_by(TranscriptSegment.start_time.asc())
            .all()
        )

        segments: List[DiarizedSegmentItem] = []
        teacher_time = 0.0
        student_time = 0.0
        teacher_count = 0
        student_count = 0

        for s in db_segments:
            dur = max(0.1, s.end_time - s.start_time)
            words = len(s.transcript_text.split())
            if s.speaker == "Teacher":
                teacher_time += dur
                teacher_count += 1
            else:
                student_time += dur
                student_count += 1

            segments.append(
                DiarizedSegmentItem(
                    segment_id=s.id,
                    speaker=s.speaker or "Teacher",
                    start_time=s.start_time,
                    end_time=s.end_time,
                    text=s.transcript_text,
                    confidence=0.94,
                    word_count=words,
                )
            )

        total_time = teacher_time + student_time
        summary = DiarizationSummary(
            total_segments=len(segments),
            teacher_segments=teacher_count,
            student_segments=student_count,
            teacher_speaking_time_sec=round(teacher_time, 2),
            student_speaking_time_sec=round(student_time, 2),
            teacher_talk_ratio=round(teacher_time / total_time, 2) if total_time > 0 else 1.0,
            total_words=transcript.total_words,
        )

        return AudioTranscriptResponse(
            session_id=session_id,
            transcript_id=transcript.id,
            has_transcript=True,
            language=transcript.language or "en",
            total_words=transcript.total_words,
            raw_text=transcript.raw_text,
            diarization_summary=summary,
            segments=segments,
        )
