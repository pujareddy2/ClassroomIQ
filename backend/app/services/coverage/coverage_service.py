"""
Main Curriculum Coverage Intelligence Engine Service.
Orchestrates coverage detection, duration calculations, rushed/over-explained classification,
sequence integrity checks, weighted coverage, remaining curriculum generation, DB persistence, and REST query APIs.
"""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.coverage_detail import CoverageDetail
from app.models.coverage_result import CoverageResult
from app.models.coverage_summary import CoverageSummary
from app.models.coverage_timeline import CoverageTimeline
from app.models.curriculum import Curriculum
from app.models.lecture_session import LectureSession
from app.models.topic import Topic
from app.services.coverage.coverage_models import (
    CoverageStatus,
    SequenceStatus,
    TopicCoverageCalculation,
)
from app.services.coverage.duration_calculator import DurationCalculator
from app.services.coverage.exceptions import (
    CurriculumNotFoundError,
    EmptyTranscriptError,
    InvalidMetadataError,
    LectureNotFoundError,
)
from app.services.coverage.partial_coverage_calculator import PartialCoverageCalculator
from app.services.coverage.remaining_curriculum_builder import RemainingCurriculumBuilder
from app.services.coverage.sequence_verifier import SequenceVerifier
from app.services.coverage.weighted_coverage_calculator import WeightedCoverageCalculator
from app.services.curriculum_hierarchy.hierarchy_service import CurriculumHierarchyService

logger = logging.getLogger(__name__)


class CoverageService:
    """Orchestrator for the Curriculum Coverage Intelligence Engine."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.hierarchy_service = CurriculumHierarchyService(db)

    def analyze_lecture_coverage(
        self,
        transcript_chunks: List[Dict[str, Any]],
        lecture_id: Optional[UUID] = None,
        curriculum_id: Optional[UUID] = None,
        course_id: Optional[str] = None,
        faculty_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Main pipeline entry point:
        Processes transcript chunks from Member 1, detects topic coverage, duration, rushed/over-explained,
        sequence integrity, weighted coverage %, remaining curriculum, and persists to PostgreSQL.
        """
        start_time = perf_counter()
        logger.info("Coverage Started: Analyzing %d transcript chunk(s)", len(transcript_chunks))

        if not transcript_chunks:
            logger.error("Empty Transcript: No chunks provided for coverage analysis")
            raise EmptyTranscriptError("Transcript chunk list cannot be empty")

        # ── Step 1 & 2: Validate Metadata & Resolve Entities ─────────────────
        if not curriculum_id:
            first_topic = self.db.query(Topic).first()
            if first_topic:
                curriculum_id = first_topic.curriculum_id
            else:
                first_curr = self.db.query(Curriculum).first()
                if not first_curr:
                    logger.error("No curriculum found in database")
                    raise CurriculumNotFoundError("No curriculum found in database for coverage analysis")
                curriculum_id = first_curr.id

        curriculum = self.db.get(Curriculum, curriculum_id)
        if not curriculum:
            raise CurriculumNotFoundError(f"Curriculum with ID '{curriculum_id}' not found")

        logger.info("Curriculum Loaded: '%s' (ID: %s)", curriculum.title, curriculum.id)

        # Resolve or create LectureSession
        if not lecture_id:
            c_id = curriculum.course_id
            f_id = faculty_id or curriculum.faculty_id

            lec = self.db.query(LectureSession).first()
            if lec:
                lecture_id = lec.id
            else:
                new_lec = LectureSession(
                    id=uuid4(),
                    course_id=c_id,
                    faculty_id=f_id,
                    lecture_date=curriculum.uploaded_at.date(),
                    duration_minutes=60,
                    classroom="Virtual / Recorded",
                )
                self.db.add(new_lec)
                self.db.flush()
                lecture_id = new_lec.id

        lecture_session = self.db.get(LectureSession, lecture_id)
        if not lecture_session:
            raise LectureNotFoundError(f"Lecture session with ID '{lecture_id}' not found")

        # ── Step 3 & 4: Load Curriculum Hierarchy & Segments ─────────────────
        segments_resp = self.hierarchy_service.get_segments(curriculum_id)
        segments = segments_resp.segments
        logger.info("Segments Loaded: %d curriculum segment(s) fetched", len(segments))

        all_topics = self.db.query(Topic).filter(Topic.curriculum_id == curriculum_id).order_by(Topic.sequence_number.asc()).all()
        if not all_topics:
            raise InvalidMetadataError(f"Curriculum '{curriculum_id}' contains no topic rows")

        # Map topics by ID and sequence
        topic_map = {t.id: t for t in all_topics}

        # ── Step 5: Group Transcript Chunks by Topic ──────────────────────────
        chunks_by_topic: Dict[UUID, List[dict]] = {t.id: [] for t in all_topics}

        for chunk in transcript_chunks:
            raw_t_id = chunk.get("topic_id")
            matched_topic_id = None
            if raw_t_id:
                try:
                    matched_topic_id = UUID(str(raw_t_id))
                except Exception:
                    pass

            if not matched_topic_id or matched_topic_id not in topic_map:
                # Match text to segment
                text_lower = chunk.get("text", "").lower()
                for seg in segments:
                    for idx, title in enumerate(seg.topic_titles):
                        if title.lower() in text_lower:
                            matched_topic_id = seg.topic_ids[idx] if idx < len(seg.topic_ids) else seg.unit_id
                            break
                    if matched_topic_id:
                        break

            if matched_topic_id and matched_topic_id in chunks_by_topic:
                chunks_by_topic[matched_topic_id].append(chunk)

        logger.info("Coverage Detection Started: Grouped chunks across %d curriculum topic(s)", len(all_topics))

        # ── Step 6 to 11: Calculate Coverage per Topic ────────────────────────
        calc_list: List[TopicCoverageCalculation] = []
        covered_topic_order_for_seq: List[Tuple[int, float]] = []

        for seq_idx, topic in enumerate(all_topics, start=1):
            m_chunks = chunks_by_topic.get(topic.id, [])
            expected_hrs = getattr(topic, "expected_hours", 1) or 1

            (
                exp_sec,
                act_sec,
                diff_sec,
                over_exp_pct,
                first_t,
                last_t,
                occ_cnt,
                duration_status,
            ) = DurationCalculator.calculate_topic_durations(m_chunks, expected_hours=expected_hrs)

            cov_pct = 0.0
            if m_chunks:
                cov_pct = PartialCoverageCalculator.calculate_percentage(
                    topic.topic_name, [], m_chunks
                )
                if first_t is not None:
                    covered_topic_order_for_seq.append((seq_idx, first_t))
            else:
                duration_status = CoverageStatus.SKIPPED

            calc_list.append(
                TopicCoverageCalculation(
                    topic_id=topic.id,
                    topic_name=topic.topic_name,
                    sequence_order=seq_idx,
                    expected_duration_seconds=exp_sec,
                    actual_duration_seconds=act_sec,
                    duration_difference_seconds=diff_sec,
                    over_explained_percentage=over_exp_pct,
                    coverage_percentage=cov_pct,
                    status=duration_status,
                    occurrence_count=occ_cnt,
                    first_mentioned_time=first_t,
                    last_mentioned_time=last_t,
                    matching_chunks=m_chunks,
                )
            )

        logger.info("Coverage Classification Finished across topics.")

        # ── Step 12: Validate Teaching Sequence Integrity ─────────────────────
        seq_mapping, sequence_score = SequenceVerifier.verify_sequence(
            covered_topic_order_for_seq, len(all_topics)
        )

        for calc in calc_list:
            if calc.sequence_order in seq_mapping:
                lec_order, seq_status = seq_mapping[calc.sequence_order]
                calc.sequence_order_in_lecture = lec_order
                calc.sequence_integrity_status = seq_status

        # ── Step 13: Calculate Weighted Curriculum Coverage ───────────────────
        weight_status_tuples = [
            (1.0, calc.status, calc.coverage_percentage) for calc in calc_list
        ]
        raw_cov_pct, weighted_cov_pct = WeightedCoverageCalculator.calculate_weighted_coverage(
            weight_status_tuples
        )

        # ── Step 14: Generate Remaining Curriculum ────────────────────────────
        topic_status_map = {calc.topic_id: calc.status for calc in calc_list}
        remaining_data = RemainingCurriculumBuilder.build_remaining_curriculum(segments, topic_status_map)

        # ── Step 15: Persist Coverage Results (Idempotent Upsert) ─────────────
        # Clear existing coverage records for lecture to avoid duplicates
        self.db.execute(delete(CoverageDetail).where(CoverageDetail.coverage_result_id.in_(
            select(CoverageResult.id).where(CoverageResult.lecture_id == lecture_id)
        )))
        self.db.execute(delete(CoverageResult).where(CoverageResult.lecture_id == lecture_id))
        self.db.execute(delete(CoverageTimeline).where(CoverageTimeline.lecture_id == lecture_id))
        self.db.flush()

        covered_count = 0
        partially_count = 0
        skipped_count = 0
        rushed_count = 0
        over_count = 0
        repeated_count = 0
        not_sched_count = 0

        timeline_items: List[CoverageTimeline] = []
        display_order = 1

        for calc in calc_list:
            if calc.status == CoverageStatus.COVERED:
                covered_count += 1
            elif calc.status == CoverageStatus.PARTIALLY_COVERED:
                partially_count += 1
            elif calc.status == CoverageStatus.SKIPPED:
                skipped_count += 1
            elif calc.status == CoverageStatus.RUSHED:
                rushed_count += 1
            elif calc.status == CoverageStatus.OVER_EXPLAINED:
                over_count += 1
            elif calc.status == CoverageStatus.REPEATED:
                repeated_count += 1
            elif calc.status == CoverageStatus.NOT_SCHEDULED:
                not_sched_count += 1

            cov_res = CoverageResult(
                id=uuid4(),
                lecture_id=lecture_id,
                curriculum_id=curriculum_id,
                topic_id=calc.topic_id,
                topic_name=calc.topic_name,
                coverage_status=calc.status.value,
                coverage_percentage=calc.coverage_percentage,
                expected_duration_seconds=calc.expected_duration_seconds,
                actual_duration_seconds=calc.actual_duration_seconds,
                duration_difference_seconds=calc.duration_difference_seconds,
                over_explained_percentage=calc.over_explained_percentage,
                first_mentioned_time=calc.first_mentioned_time,
                last_mentioned_time=calc.last_mentioned_time,
                occurrence_count=calc.occurrence_count,
                sequence_order_in_curriculum=calc.sequence_order,
                sequence_order_in_lecture=calc.sequence_order_in_lecture,
                sequence_integrity_status=calc.sequence_integrity_status.value,
            )
            self.db.add(cov_res)
            self.db.flush()

            for chunk in calc.matching_chunks:
                c_id_str = str(chunk.get("chunk_id", uuid4()))
                snippet = chunk.get("text", "")[:100]
                cov_det = CoverageDetail(
                    id=uuid4(),
                    coverage_result_id=cov_res.id,
                    chunk_id=c_id_str,
                    start_time=float(chunk.get("start_time", 0.0)),
                    end_time=float(chunk.get("end_time", 0.0)),
                    speaker=chunk.get("speaker", "Faculty"),
                    text_snippet=snippet,
                    relevance_score=1.0,
                )
                self.db.add(cov_det)

                # Create timeline interval
                timeline_items.append(
                    CoverageTimeline(
                        id=uuid4(),
                        lecture_id=lecture_id,
                        topic_id=calc.topic_id,
                        topic_name=calc.topic_name,
                        start_time=float(chunk.get("start_time", 0.0)),
                        end_time=float(chunk.get("end_time", 0.0)),
                        duration_seconds=max(0.0, float(chunk.get("end_time", 0.0)) - float(chunk.get("start_time", 0.0))),
                        status=calc.status.value,
                        display_order=display_order,
                    )
                )
                display_order += 1

        for tl in timeline_items:
            self.db.add(tl)

        logger.info("Timeline Generated: %d interval(s) created", len(timeline_items))

        # Upsert CoverageSummary
        existing_summary = self.db.query(CoverageSummary).filter(CoverageSummary.lecture_id == lecture_id).first()
        if existing_summary:
            existing_summary.total_topics = len(all_topics)
            existing_summary.covered_topics = covered_count
            existing_summary.partially_covered = partially_count
            existing_summary.skipped_topics = skipped_count
            existing_summary.rushed_topics = rushed_count
            existing_summary.over_explained = over_count
            existing_summary.repeated_topics = repeated_count
            existing_summary.not_scheduled = not_sched_count
            existing_summary.raw_coverage_percentage = raw_cov_pct
            existing_summary.weighted_coverage_percentage = weighted_cov_pct
            existing_summary.remaining_topics_count = len(remaining_data["remaining_topics"])
            existing_summary.sequence_score = sequence_score
            existing_summary.processing_time_seconds = round(perf_counter() - start_time, 2)
        else:
            summary = CoverageSummary(
                id=uuid4(),
                lecture_id=lecture_id,
                curriculum_id=curriculum_id,
                total_topics=len(all_topics),
                covered_topics=covered_count,
                partially_covered=partially_count,
                skipped_topics=skipped_count,
                rushed_topics=rushed_count,
                over_explained=over_count,
                repeated_topics=repeated_count,
                not_scheduled=not_sched_count,
                raw_coverage_percentage=raw_cov_pct,
                weighted_coverage_percentage=weighted_cov_pct,
                remaining_topics_count=len(remaining_data["remaining_topics"]),
                sequence_score=sequence_score,
                processing_time_seconds=round(perf_counter() - start_time, 2),
            )
            self.db.add(summary)

        self.db.flush()
        logger.info("Coverage Stored: Saved summary & details for lecture %s", lecture_id)

        return {
            "status": "SUCCESS",
            "lecture_id": str(lecture_id),
            "covered_topics": covered_count,
            "partially_covered": partially_count,
            "skipped_topics": skipped_count,
            "rushed_topics": rushed_count,
            "over_explained": over_count,
            "repeated_topics": repeated_count,
            "weighted_coverage": weighted_cov_pct,
            "remaining_topics": len(remaining_data["remaining_topics"]),
        }

    # ── Retrieval API Methods ───────────────────────────────────────────────────

    def get_lecture_coverage(self, lecture_id: UUID) -> Dict[str, Any]:
        """GET /coverage/{lecture_id} — Overall lecture coverage."""
        summary = self.db.query(CoverageSummary).filter(CoverageSummary.lecture_id == lecture_id).first()
        if not summary:
            raise LectureNotFoundError(f"No coverage summary found for lecture '{lecture_id}'")

        return {
            "lecture_id": str(summary.lecture_id),
            "curriculum_id": str(summary.curriculum_id),
            "total_topics": summary.total_topics,
            "covered_topics": summary.covered_topics,
            "partially_covered": summary.partially_covered,
            "skipped_topics": summary.skipped_topics,
            "rushed_topics": summary.rushed_topics,
            "over_explained": summary.over_explained,
            "repeated_topics": summary.repeated_topics,
            "raw_coverage": summary.raw_coverage_percentage,
            "weighted_coverage": summary.weighted_coverage_percentage,
            "remaining_topics": summary.remaining_topics_count,
            "sequence_score": summary.sequence_score,
        }

    def get_topic_coverage(self, lecture_id: UUID) -> List[Dict[str, Any]]:
        """GET /coverage/{lecture_id}/topics — Topic level coverage results."""
        stmt = (
            select(CoverageResult)
            .where(CoverageResult.lecture_id == lecture_id)
            .order_by(CoverageResult.sequence_order_in_curriculum.asc())
        )
        results = self.db.execute(stmt).scalars().all()
        if not results:
            raise LectureNotFoundError(f"No topic coverage records found for lecture '{lecture_id}'")

        output = []
        for r in results:
            output.append({
                "id": str(r.id),
                "lecture_id": str(r.lecture_id),
                "curriculum_id": str(r.curriculum_id),
                "topic_id": str(r.topic_id),
                "topic_name": r.topic_name,
                "coverage_status": r.coverage_status,
                "coverage_percentage": r.coverage_percentage,
                "expected_duration_seconds": r.expected_duration_seconds,
                "actual_duration_seconds": r.actual_duration_seconds,
                "duration_difference_seconds": r.duration_difference_seconds,
                "over_explained_percentage": r.over_explained_percentage,
                "first_mentioned_time": r.first_mentioned_time,
                "last_mentioned_time": r.last_mentioned_time,
                "occurrence_count": r.occurrence_count,
                "sequence_order_in_curriculum": r.sequence_order_in_curriculum,
                "sequence_order_in_lecture": r.sequence_order_in_lecture,
                "sequence_integrity_status": r.sequence_integrity_status,
            })
        return output

    def get_remaining_curriculum(self, lecture_id: UUID) -> Dict[str, Any]:
        """GET /coverage/{lecture_id}/remaining — Remaining units, chapters, topics, learning outcomes."""
        summary = self.db.query(CoverageSummary).filter(CoverageSummary.lecture_id == lecture_id).first()
        if not summary:
            raise LectureNotFoundError(f"No coverage summary found for lecture '{lecture_id}'")

        segments_resp = self.hierarchy_service.get_segments(summary.curriculum_id)
        segments = segments_resp.segments

        results = self.db.query(CoverageResult).filter(CoverageResult.lecture_id == lecture_id).all()
        topic_status_map = {r.topic_id: CoverageStatus(r.coverage_status) for r in results}

        return RemainingCurriculumBuilder.build_remaining_curriculum(segments, topic_status_map)

    def get_coverage_timeline(self, lecture_id: UUID) -> Dict[str, Any]:
        """GET /coverage/{lecture_id}/timeline — Chronological timeline intervals."""
        stmt = (
            select(CoverageTimeline)
            .where(CoverageTimeline.lecture_id == lecture_id)
            .order_by(CoverageTimeline.start_time.asc())
        )
        timelines = self.db.execute(stmt).scalars().all()
        if not timelines:
            summary = self.db.query(CoverageSummary).filter(CoverageSummary.lecture_id == lecture_id).first()
            if not summary:
                raise LectureNotFoundError(f"No coverage timeline records found for lecture '{lecture_id}'")
            return {"lecture_id": str(lecture_id), "intervals": [], "total_intervals": 0}

        intervals = [
            {
                "id": str(t.id),
                "topic_id": str(t.topic_id) if t.topic_id else None,
                "topic_name": t.topic_name,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "duration_seconds": t.duration_seconds,
                "status": t.status,
                "display_order": t.display_order,
            }
            for t in timelines
        ]
        return {
            "status": "SUCCESS",
            "lecture_id": str(lecture_id),
            "total_intervals": len(intervals),
            "intervals": intervals,
        }

    def get_coverage_summary(self, lecture_id: UUID) -> Dict[str, Any]:
        """GET /coverage/{lecture_id}/summary — Full summary analytics."""
        return self.get_lecture_coverage(lecture_id)

    def get_coverage_history(
        self,
        curriculum_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        GET /api/v1/coverage/history?curriculum_id=
        Returns paginated list of coverage summaries across all lectures for a curriculum.
        """
        import math
        from sqlalchemy import func as sqlfunc

        stmt = (
            select(CoverageSummary)
            .where(CoverageSummary.curriculum_id == curriculum_id)
            .order_by(CoverageSummary.created_at.desc())
        )
        count_stmt = select(sqlfunc.count()).select_from(stmt.subquery())
        total_items = int(self.db.execute(count_stmt).scalar_one())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        summaries = self.db.execute(stmt).scalars().all()

        total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1

        items = [
            {
                "lecture_id": str(s.lecture_id),
                "curriculum_id": str(s.curriculum_id),
                "total_topics": s.total_topics,
                "covered_topics": s.covered_topics,
                "partially_covered": s.partially_covered,
                "skipped_topics": s.skipped_topics,
                "weighted_coverage": s.weighted_coverage_percentage,
                "sequence_score": s.sequence_score,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in summaries
        ]

        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }
