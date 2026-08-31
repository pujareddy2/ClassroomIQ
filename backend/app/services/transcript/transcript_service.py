"""
Main Transcript Intelligence Service.
Orchestrates raw transcript ingestion, cleaning, sentence segmentation, semantic chunking,
curriculum mapping from PostgreSQL, database persistence, and statistics generation.
"""

from __future__ import annotations

import logging
from datetime import date
from time import perf_counter
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.curriculum import Curriculum
from app.models.faculty import Faculty
from app.models.lecture_session import LectureSession
from app.models.transcript import Transcript
from app.models.transcript_chunk import TranscriptChunk
from app.models.transcript_segment import TranscriptSegment
from app.models.transcript_topic_mapping import TranscriptTopicMapping
from app.services.curriculum_hierarchy.exceptions import EmptyCurriculumError
from app.services.curriculum_hierarchy.hierarchy_service import CurriculumHierarchyService
from app.services.transcript.chunk_builder import ChunkData, SemanticChunkBuilder
from app.services.transcript.curriculum_mapper import CurriculumMapper, MappingResult
from app.services.transcript.exceptions import (
    EmptyTranscriptError,
    LectureNotFoundError,
    TranscriptValidationError,
)
from app.services.transcript.mapping_validator import MappingValidator
from app.services.transcript.sentence_segmenter import SentenceItem, SentenceSegmenter
from app.services.transcript.transcript_cleaner import TranscriptCleaner
from app.services.transcript.transcript_statistics import (
    TranscriptStatistics,
    TranscriptStatisticsCalculator,
)

logger = logging.getLogger(__name__)


class TranscriptService:
    """Service for processing audio/video transcripts and mapping them to PostgreSQL curriculum topics."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.hierarchy_service = CurriculumHierarchyService(db)

    def process_and_store_transcript(
        self,
        lecture_id: UUID | None,
        course_name_or_code: str,
        faculty_name: str,
        transcript_data: List[Dict[str, Any]],
        curriculum_id: UUID | None = None,
        lecture_date: date | None = None,
    ) -> Dict[str, Any]:
        start_time = perf_counter()
        logger.info("Transcript Received: %d entry/entries in payload", len(transcript_data))

        if not transcript_data:
            raise EmptyTranscriptError("Transcript array cannot be empty")

        # ── Step 2 & 3: Resolve / Create Lecture Session ──────────────────────
        lecture: LectureSession | None = None
        if lecture_id is not None:
            lecture = self.db.get(LectureSession, UUID(str(lecture_id)))

        if lecture is None:
            # Resolve faculty and course
            faculty = self.db.query(Faculty).join(Faculty.user).filter(
                Faculty.user.has(full_name=faculty_name.strip())
            ).first()
            if not faculty:
                # Fallback to first available faculty
                faculty = self.db.query(Faculty).first()
                if not faculty:
                    raise LectureNotFoundError(f"Faculty '{faculty_name}' not found")

            course = self.db.query(Course).filter(
                (Course.course_code.ilike(course_name_or_code.strip())) |
                (Course.course_name.ilike(course_name_or_code.strip()))
            ).first()
            if not course:
                course = self.db.query(Course).first()
                if not course:
                    raise LectureNotFoundError(f"Course '{course_name_or_code}' not found")

            lecture = LectureSession(
                course_id=course.id,
                faculty_id=faculty.id,
                lecture_date=lecture_date or date.today(),
                duration_minutes=int((transcript_data[-1].get("end", 0.0)) // 60) or 60,
                classroom="Virtual / Recorded",
            )
            self.db.add(lecture)
            self.db.flush()

        logger.info("Lecture Metadata Resolved: ID %s", lecture.id)

        # ── Step 4: Store Original Transcript ─────────────────────────────────
        raw_lines = []
        for item in transcript_data:
            spk = str(item.get('speaker', 'Faculty')).replace('\x00', '')
            txt = str(item.get('text', '')).replace('\x00', '')
            raw_lines.append(f"{spk}: {txt}")
        raw_full_text = "\n".join(raw_lines).replace("\x00", "")

        transcript_record = Transcript(
            lecture_id=lecture.id,
            language="en",
            total_words=len(raw_full_text.split()),
            raw_text=raw_full_text,
            cleaned_text="",
        )
        self.db.add(transcript_record)
        self.db.flush()
        logger.info("Transcript Stored: ID %s", transcript_record.id)

        # ── Step 5: Clean Transcript ───────────────────────────────────────────
        cleaned_text = TranscriptCleaner.clean_text(raw_full_text)
        transcript_record.cleaned_text = cleaned_text
        self.db.add(transcript_record)
        self.db.flush()
        logger.info("Cleaning Completed: Cleaned length = %d characters", len(cleaned_text))

        # ── Step 6: Sentence Segmentation ─────────────────────────────────────
        sentences: List[SentenceItem] = SentenceSegmenter.segment(transcript_data)
        logger.info("Segmentation Completed: %d sentence(s) extracted", len(sentences))

        # ── Step 7: Semantic Chunk Creation ───────────────────────────────────
        chunks: List[ChunkData] = SemanticChunkBuilder.build_chunks(sentences)
        logger.info("Chunking Completed: %d semantic chunk(s) built", len(chunks))

        # ── Step 8 & 9: Load Curriculum Hierarchy & Segments from DB ─────────
        if curriculum_id is None:
            # Find latest parsed curriculum for course
            curr = self.db.query(Curriculum).filter(
                Curriculum.course_id == lecture.course_id,
                Curriculum.processing_status == "PARSED"
            ).order_by(Curriculum.created_at.desc()).first()
            if not curr:
                curr = self.db.query(Curriculum).order_by(Curriculum.created_at.desc()).first()
            if curr:
                curriculum_id = curr.id

        segments = []
        if curriculum_id is not None:
            try:
                seg_response = self.hierarchy_service.get_segments(curriculum_id)
                segments = seg_response.segments
                logger.info("Curriculum Loaded: %d curriculum segment(s) fetched for curriculum %s", len(segments), curriculum_id)
            except EmptyCurriculumError:
                logger.warning("Curriculum '%s' has no topic nodes yet — transcript will be stored without topic mappings.", curriculum_id)
        else:
            logger.warning("No Curriculum found for course. Mapping will mark chunks as unmapped.")

        # ── Step 10: Map Transcript Chunks to Curriculum Segments ────────────
        logger.info("Mapping Started...")
        mappings: List[MappingResult] = CurriculumMapper.map_chunks(chunks, segments)
        logger.info("Mapping Finished: %d mapping result(s) generated", len(mappings))

        # ── Step 11: Persist Chunks and Topic Mappings to PostgreSQL ──────────
        chunk_orm_map: Dict[int, TranscriptChunk] = {}
        for c in chunks:
            c_orm = TranscriptChunk(
                transcript_id=transcript_record.id,
                chunk_index=c.chunk_index,
                start_time=c.start_time,
                end_time=c.end_time,
                speaker=c.speaker,
                text=c.text,
                sentence_count=c.sentence_count,
                word_count=c.word_count,
            )
            self.db.add(c_orm)
            self.db.flush()
            chunk_orm_map[c.chunk_index] = c_orm

            # Also populate legacy TranscriptSegment row for full backward compatibility
            top_id = mappings[c.chunk_index - 1].topic_id if (c.chunk_index - 1) < len(mappings) else None
            t_seg = TranscriptSegment(
                transcript_id=transcript_record.id,
                topic_id=top_id,
                start_time=c.start_time,
                end_time=c.end_time,
                speaker=c.speaker,
                transcript_text=c.text,
            )
            self.db.add(t_seg)

        mapping_orm_list: List[TranscriptTopicMapping] = []
        for m in mappings:
            chunk_obj = chunk_orm_map.get(m.chunk_index)
            if chunk_obj is None:
                continue

            mapping_orm = TranscriptTopicMapping(
                lecture_id=lecture.id,
                transcript_id=transcript_record.id,
                chunk_id=chunk_obj.id,
                curriculum_id=m.curriculum_id,
                unit_id=m.unit_id,
                chapter_id=m.chapter_id,
                topic_id=m.topic_id,
                confidence_score=m.confidence_score,
                mapping_reason=m.mapping_reason,
            )
            self.db.add(mapping_orm)
            mapping_orm_list.append(mapping_orm)

        self.db.flush()
        logger.info("Database Saved: %d chunks and %d mappings persisted into PostgreSQL", len(chunk_orm_map), len(mapping_orm_list))

        # ── Step 12: Generate Statistics & Warnings ───────────────────────────
        warnings = MappingValidator.validate(transcript_data, chunks, mappings)
        stats = TranscriptStatisticsCalculator.calculate(sentences, chunks, mappings, warnings)

        elapsed = perf_counter() - start_time
        logger.info("Execution Time: %.4f seconds for lecture ID %s", elapsed, lecture.id)

        return {
            "status": "SUCCESS",
            "lecture_id": str(lecture.id),
            "transcript_id": str(transcript_record.id),
            "chunks": len(chunks),
            "mapped_chunks": stats.mapped_chunks,
            "unmapped_chunks": stats.unmapped_chunks,
            "processing_time": f"{round(elapsed, 2)} sec",
            "statistics": stats.model_dump(),
        }

    def get_lecture(self, lecture_id: UUID) -> Dict[str, Any]:
        lecture = self.db.get(LectureSession, lecture_id)
        if not lecture:
            raise LectureNotFoundError(f"Lecture '{lecture_id}' not found")

        transcript = self.db.query(Transcript).filter(Transcript.lecture_id == lecture_id).first()
        return {
            "lecture_id": str(lecture.id),
            "course_id": str(lecture.course_id),
            "faculty_id": str(lecture.faculty_id),
            "lecture_date": str(lecture.lecture_date),
            "duration_minutes": lecture.duration_minutes,
            "classroom": lecture.classroom,
            "has_transcript": transcript is not None,
            "transcript_id": str(transcript.id) if transcript else None,
        }

    def get_lecture_chunks(self, lecture_id: UUID, limit: int = 500) -> List[Dict[str, Any]]:
        transcript = self.db.query(Transcript).filter(Transcript.lecture_id == lecture_id).first()
        if not transcript:
            raise LectureNotFoundError(f"Transcript for lecture '{lecture_id}' not found")

        query = self.db.query(TranscriptChunk).filter(
            TranscriptChunk.transcript_id == transcript.id
        ).order_by(TranscriptChunk.chunk_index)
        if limit:
            query = query.limit(limit)
        chunks = query.all()

        return [
            {
                "chunk_id": str(c.id),
                "chunk_index": c.chunk_index,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "speaker": c.speaker,
                "text": c.text,
                "sentence_count": c.sentence_count,
                "word_count": c.word_count,
            }
            for c in chunks
        ]

    def get_lecture_mappings(self, lecture_id: UUID) -> List[Dict[str, Any]]:
        mappings = self.db.query(TranscriptTopicMapping).filter(
            TranscriptTopicMapping.lecture_id == lecture_id
        ).all()

        return [
            {
                "mapping_id": str(m.id),
                "chunk_id": str(m.chunk_id),
                "curriculum_id": str(m.curriculum_id),
                "unit_id": str(m.unit_id) if m.unit_id else None,
                "chapter_id": str(m.chapter_id) if m.chapter_id else None,
                "topic_id": str(m.topic_id),
                "confidence_score": m.confidence_score,
                "mapping_reason": m.mapping_reason,
            }
            for m in mappings
        ]

    def get_lecture_statistics(self, lecture_id: UUID) -> Dict[str, Any]:
        transcript = self.db.query(Transcript).filter(Transcript.lecture_id == lecture_id).first()
        if not transcript:
            raise LectureNotFoundError(f"Transcript for lecture '{lecture_id}' not found")

        chunks = self.db.query(TranscriptChunk).filter(TranscriptChunk.transcript_id == transcript.id).all()
        mappings = self.db.query(TranscriptTopicMapping).filter(TranscriptTopicMapping.lecture_id == lecture_id).all()

        mapped_count = sum(1 for m in mappings if m.confidence_score >= 0.30)
        total_chunks = len(chunks)
        unmapped_count = total_chunks - mapped_count
        coverage_candidates = sum(1 for m in mappings if m.confidence_score >= 0.60)

        total_words = sum(c.word_count for c in chunks)
        avg_words = round(total_words / total_chunks, 1) if total_chunks > 0 else 0.0
        avg_time = round((chunks[-1].end_time - chunks[0].start_time) / total_chunks, 1) if chunks else 0.0

        return {
            "lecture_id": str(lecture_id),
            "total_sentences": sum(c.sentence_count for c in chunks),
            "total_chunks": total_chunks,
            "mapped_chunks": mapped_count,
            "unmapped_chunks": unmapped_count,
            "coverage_candidates": coverage_candidates,
            "average_chunk_length_words": avg_words,
            "average_speaking_time_seconds": avg_time,
        }

    def get_lecture_status(self, lecture_id: UUID) -> dict:
        """GET /lecture/{lecture_id}/status — Processing pipeline status."""
        from app.models.coverage_summary import CoverageSummary
        from app.models.validation_summary import ValidationSummary

        lecture = self.db.get(LectureSession, lecture_id)
        if not lecture:
            raise LectureNotFoundError(f"Lecture '{lecture_id}' not found")

        transcript = self.db.query(Transcript).filter(Transcript.lecture_id == lecture_id).first()
        has_transcript = transcript is not None

        has_coverage = self.db.query(CoverageSummary).filter(
            CoverageSummary.lecture_id == lecture_id
        ).first() is not None

        has_validation = self.db.query(ValidationSummary).filter(
            ValidationSummary.lecture_id == lecture_id
        ).first() is not None

        processing_complete = has_transcript and has_coverage and has_validation

        if processing_complete:
            status_label = "COMPLETE"
        elif has_validation:
            status_label = "VALIDATION_READY"
        elif has_coverage:
            status_label = "COVERAGE_READY"
        elif has_transcript:
            status_label = "TRANSCRIPT_READY"
        else:
            status_label = "PENDING"

        return {
            "lecture_id": str(lecture_id),
            "has_transcript": has_transcript,
            "has_coverage": has_coverage,
            "has_validation": has_validation,
            "processing_complete": processing_complete,
            "status": status_label,
        }
