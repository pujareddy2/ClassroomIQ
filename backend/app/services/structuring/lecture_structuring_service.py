"""
Lecture Structuring & Media Synchronization Service.
Orchestrates Audio Intelligence, Video Intelligence, and Slide processing to output
the definitive Member 1 -> Member 2 Structured Lecture Handover Asset.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lecture_session import LectureSession
from app.models.recording import Recording
from app.models.transcript import Transcript
from app.models.transcript_segment import TranscriptSegment
from app.schemas.audio import TranscriptSegmentItem
from app.schemas.structuring import (
    LectureStructureProcessRequest,
    LectureStructuringMetadata,
    StructuredLectureResponse,
    TopicSegmentItem,
)
from app.schemas.video import VideoProcessRequest, VisualTimelineEvent
from app.services.audio.audio_intelligence_service import AudioIntelligenceService
from app.services.multimedia.slide_processor import SlideProcessor
from app.services.multimedia.storage_service import MultimediaStorageService
from app.services.structuring.lecture_metadata_extractor import LectureMetadataExtractor
from app.services.structuring.media_synchronizer import MediaSynchronizer
from app.services.structuring.topic_segmenter import TopicSegmenter
from app.services.video.video_intelligence_service import VideoIntelligenceService

logger = logging.getLogger(__name__)


class LectureStructuringService:
    """Orchestrates multi-modal lecture structuring, chapter segmentation, and media synchronization."""

    def __init__(
        self,
        db: Optional[Session] = None,
        storage_service: Optional[MultimediaStorageService] = None,
    ):
        self.db = db
        self.storage = storage_service or MultimediaStorageService()
        self.audio_service = AudioIntelligenceService(db=db, storage_service=self.storage)
        self.video_service = VideoIntelligenceService(storage_service=self.storage)
        self.slide_processor = SlideProcessor()
        self.synchronizer = MediaSynchronizer()
        self.topic_segmenter = TopicSegmenter()
        self.metadata_extractor = LectureMetadataExtractor()

    def process_and_structure_lecture(
        self,
        session_id: UUID,
        request: Optional[LectureStructureProcessRequest] = None,
        db: Optional[Session] = None,
    ) -> StructuredLectureResponse:
        """
        Executes end-to-end multi-modal structuring for a lecture session.
        Combines Audio Transcription, Diarization, Video Visual Timeline, and Slide Decks.
        """
        cfg = request or LectureStructureProcessRequest()
        active_db = db or self.db
        session_dir = self.storage.get_session_dir(session_id)

        # 1. Fetch Session Metadata from DB or JSON
        course_name = "Computer Science / Advanced Systems"
        faculty_name = "Prof. Lead Instructor"
        lecture_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if active_db:
            session_model = active_db.get(LectureSession, session_id)
            if session_model:
                lecture_date = str(session_model.lecture_date)
                if session_model.course:
                    course_name = session_model.course.course_name
                if session_model.faculty and session_model.faculty.user:
                    faculty_name = session_model.faculty.user.full_name

        # 2. Extract or Load Audio Transcript Segments
        transcript_segments: List[TranscriptSegmentItem] = []
        # First check DB or cached transcript
        if active_db:
            db_transcript = active_db.query(Transcript).filter(Transcript.lecture_id == session_id).first()
            if db_transcript and db_transcript.transcript_segments:
                transcript_segments = [
                    TranscriptSegmentItem(
                        start_time=s.start_time,
                        end_time=s.end_time,
                        speaker=s.speaker or "Teacher",
                        text=s.transcript_text,
                    )
                    for s in db_transcript.transcript_segments
                ]

        if not transcript_segments:
            try:
                audio_res = self.audio_service.process_session_audio(session_id)
                transcript_segments = audio_res.segments
            except Exception as exc:
                logger.warning("Audio processing for structuring fallback: %s", exc)

        # 3. Extract or Load Video Intelligence Timeline
        visual_events: List[VisualTimelineEvent] = []
        video_summary = None
        video_res = self.video_service.get_session_video(session_id)
        if video_res and video_res.timeline:
            visual_events = video_res.timeline
            video_summary = video_res.summary
        else:
            try:
                video_res = self.video_service.process_session_video(session_id)
                visual_events = video_res.timeline
                video_summary = video_res.summary
            except Exception as exc:
                logger.warning("Video processing for structuring fallback: %s", exc)

        # 4. Extract or Load Presentation Slides
        slides: List[Dict[str, Any]] = []
        slide_files = list((session_dir / "slides").glob("*.pdf")) + list((session_dir / "slides").glob("*.pptx"))
        if not slide_files:
            slide_files = list(session_dir.glob("**/*.pdf")) + list(session_dir.glob("**/*.pptx"))

        if slide_files:
            try:
                slides = self.slide_processor.process_presentation(slide_files[0], session_dir / "slides")
            except Exception as e:
                logger.warning("Slide extraction failed for structuring: %s", e)


        # Determine total duration
        total_duration = 0.0
        if transcript_segments:
            total_duration = max(total_duration, transcript_segments[-1].end_sec)
        if visual_events:
            total_duration = max(total_duration, visual_events[-1].end_time_sec)
        if total_duration == 0.0:
            total_duration = 60.0

        # 5. Run Multi-Track Media Synchronizer
        sync_timeline = self.synchronizer.build_synchronized_timeline(
            transcript_segments=transcript_segments,
            visual_events=visual_events,
            slides=slides,
            total_duration_sec=total_duration,
            resolution_sec=cfg.sync_resolution_sec,
        )

        # 6. Run Semantic Topic Segmenter
        topic_segments = self.topic_segmenter.segment_lecture(
            transcript_segments=transcript_segments,
            visual_events=visual_events,
            slides=slides,
            min_segment_duration_sec=cfg.min_topic_duration_sec,
        )

        # 7. Extract Multi-Modal Metadata & Speaking Pace
        metadata = self.metadata_extractor.extract_metadata(
            transcript_segments=transcript_segments,
            topic_segments=topic_segments,
            video_summary=video_summary,
            total_duration_sec=total_duration,
        )

        # 8. Optional: Persist to PostgreSQL Database
        if cfg.auto_persist_db and active_db:
            self._persist_to_database(active_db, session_id, transcript_segments)

        res = StructuredLectureResponse(
            session_id=session_id,
            course_name=course_name,
            faculty_name=faculty_name,
            lecture_date=lecture_date,
            status="STRUCTURED",
            metadata=metadata,
            topic_segments=topic_segments,
            synchronized_timeline=sync_timeline,
            transcript_segments=transcript_segments,
            visual_events=visual_events,
            slides_count=len(slides),
            structured_at=datetime.now(timezone.utc).isoformat(),
        )

        # Cache on disk
        try:
            cache_file = session_dir / "structured_lecture.json"
            cache_file.write_text(res.model_dump_json(indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Could not persist structured_lecture.json: %s", e)

        return res

    def get_structured_lecture(
        self,
        session_id: UUID,
        db: Optional[Session] = None,
    ) -> StructuredLectureResponse:
        """Retrieves existing structured lecture data or compiles instant alignment from existing assets without re-running heavy inference."""
        session_dir = self.storage.get_session_dir(session_id)
        cache_file = session_dir / "structured_lecture.json"
        if cache_file.exists():
            try:
                import json
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                return StructuredLectureResponse.model_validate(data)
            except Exception as e:
                logger.warning("Failed to load cached structured lecture for %s: %s", session_id, e)

        active_db = db or self.db
        # 1. Fetch Session Metadata
        course_name = "Computer Science / Advanced Systems"
        faculty_name = "Prof. Lead Instructor"
        lecture_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if active_db:
            session_model = active_db.get(LectureSession, session_id)
            if session_model:
                lecture_date = str(session_model.lecture_date)
                if session_model.course:
                    course_name = session_model.course.course_name
                if session_model.faculty and session_model.faculty.user:
                    faculty_name = session_model.faculty.user.full_name

        # 2. Load existing transcript (fast, no inference)
        transcript_resp = self.audio_service.get_session_transcript(session_id)
        transcript_segments = transcript_resp.segments

        # 3. Load existing video timeline (fast, no inference)
        video_res = self.video_service.get_session_video(session_id)
        visual_events = video_res.timeline
        video_summary = video_res.summary

        # 4. Load slides
        slides: List[Dict[str, Any]] = []
        slide_files = list((session_dir / "slides").glob("*.pdf")) + list((session_dir / "slides").glob("*.pptx"))
        if not slide_files:
            slide_files = list(session_dir.glob("**/*.pdf")) + list(session_dir.glob("**/*.pptx"))
        if slide_files:
            try:
                slides = self.slide_processor.process_presentation(slide_files[0], session_dir / "slides")
            except Exception:
                pass

        total_duration = 0.0
        if transcript_segments:
            total_duration = max(total_duration, transcript_segments[-1].end_sec)
        if visual_events:
            total_duration = max(total_duration, visual_events[-1].end_time_sec)
        if total_duration == 0.0:
            total_duration = 60.0

        sync_timeline = self.synchronizer.build_synchronized_timeline(
            transcript_segments=transcript_segments,
            visual_events=visual_events,
            slides=slides,
            total_duration_sec=total_duration,
            resolution_sec=2.0,
        )

        topic_segments = self.topic_segmenter.segment_lecture(
            transcript_segments=transcript_segments,
            visual_events=visual_events,
            slides=slides,
            min_segment_duration_sec=15.0,
        )

        metadata = self.metadata_extractor.extract_metadata(
            transcript_segments=transcript_segments,
            topic_segments=topic_segments,
            video_summary=video_summary,
            total_duration_sec=total_duration,
        )

        return StructuredLectureResponse(
            session_id=session_id,
            course_name=course_name,
            faculty_name=faculty_name,
            lecture_date=lecture_date,
            status="STRUCTURED" if (transcript_segments or visual_events) else "READY_TO_STRUCTURE",
            metadata=metadata,
            topic_segments=topic_segments,
            synchronized_timeline=sync_timeline,
            transcript_segments=transcript_segments,
            visual_events=visual_events,
            slides_count=len(slides),
            structured_at=datetime.now(timezone.utc).isoformat(),
        )

    def _persist_to_database(
        self,
        db: Session,
        session_id: UUID,
        segments: List[TranscriptSegmentItem],
    ) -> None:
        """Saves transcript record and transcript segment items to PostgreSQL."""
        try:
            transcript = db.query(Transcript).filter(Transcript.lecture_id == session_id).first()
            if not transcript:
                raw_full = " ".join(s.text for s in segments)
                transcript = Transcript(
                    lecture_id=session_id,
                    language="en",
                    total_words=len(raw_full.split()),
                    raw_text=raw_full,
                    cleaned_text=raw_full,
                )
                db.add(transcript)
                db.flush()

            # Insert segment rows if not already present
            existing_count = db.query(TranscriptSegment).filter(TranscriptSegment.transcript_id == transcript.id).count()
            if existing_count == 0 and segments:
                for seg in segments:
                    db.add(
                        TranscriptSegment(
                            transcript_id=transcript.id,
                            start_time=seg.start_sec,
                            end_time=seg.end_sec,
                            speaker=seg.speaker,
                            transcript_text=seg.text,
                        )
                    )
                db.commit()
                logger.info("Persisted %d transcript segments to database for session %s", len(segments), session_id)
        except Exception as exc:
            db.rollback()
            logger.warning("Database persistence for structured transcript skipped: %s", exc)

