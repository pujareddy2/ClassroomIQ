"""
Teaching Service — Orchestrates Teaching Intelligence, prerequisite checking, idempotency, and DB persistence.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coverage_summary import CoverageSummary
from app.models.teaching_intelligence import (
    TeachingAnalysis,
    TeachingExample,
    TeachingExplanation,
    TeachingInteraction,
    TeachingStructure,
    TeachingSummary,
)
from app.models.transcript_chunk import TranscriptChunk
from app.models.validation_summary import ValidationSummary
from app.repositories.teaching_repository import TeachingRepository
from app.schemas.teaching import (
    TeachingAnalyzeData,
    TeachingAnalyzeRequest,
    TeachingExampleItem,
    TeachingExamplesResponse,
    TeachingInteractionResponse,
    TeachingStructureResponse,
    TeachingStrengthsResponse,
    TeachingSummaryResponse,
    TeachingWeaknessesResponse,
)
from app.services.teaching.example_engine import ExampleEngine
from app.services.teaching.explanation_engine import ExplanationEngine
from app.services.teaching.interaction_engine import InteractionEngine
from app.services.teaching.scoring_engine import ScoringEngine
from app.services.teaching.structure_engine import StructureEngine

logger = logging.getLogger(__name__)


class TeachingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TeachingRepository(db)
        self.explanation_engine = ExplanationEngine()
        self.example_engine = ExampleEngine()
        self.structure_engine = StructureEngine()
        self.interaction_engine = InteractionEngine()
        self.scoring_engine = ScoringEngine()

    def analyze_lecture_teaching(self, payload: TeachingAnalyzeRequest) -> TeachingAnalyzeData:
        logger.info("Teaching Analysis Started for lecture_id=%s", payload.lecture_id)

        # Guarantee parent ORM entities exist for FK constraints
        self._ensure_parent_records(payload.lecture_id, payload.curriculum_id, payload.faculty_id)

        # Load Coverage & Validation Summaries if present
        coverage_summary = None
        if payload.coverage_summary_id:
            coverage_summary = self.db.get(CoverageSummary, payload.coverage_summary_id)
        else:
            stmt = select(CoverageSummary).where(CoverageSummary.lecture_id == payload.lecture_id)
            coverage_summary = self.db.execute(stmt).scalar_one_or_none()

        validation_summary = None
        if payload.validation_summary_id:
            validation_summary = self.db.get(ValidationSummary, payload.validation_summary_id)
        else:
            stmt = select(ValidationSummary).where(ValidationSummary.lecture_id == payload.lecture_id)
            validation_summary = self.db.execute(stmt).scalar_one_or_none()

        cov_summary_id = coverage_summary.id if coverage_summary else payload.coverage_summary_id
        val_summary_id = validation_summary.id if validation_summary else payload.validation_summary_id

        logger.info("Coverage Loaded: %s, Validation Loaded: %s", cov_summary_id, val_summary_id)

        # Load transcript chunks
        transcript_chunks: List[Dict[str, Any]] = []
        if payload.transcript_chunks:
            transcript_chunks = [c.model_dump() for c in payload.transcript_chunks]
        else:
            stmt = (
                select(TranscriptChunk)
                .where(TranscriptChunk.lecture_id == payload.lecture_id)
                .order_by(TranscriptChunk.chunk_index)
            )
            chunks_orm = self.db.execute(stmt).scalars().all()
            for chunk in chunks_orm:
                transcript_chunks.append(
                    {
                        "chunk_id": str(chunk.id),
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time,
                        "speaker": chunk.speaker or "Faculty",
                        "text": chunk.text,
                        "topic_id": str(chunk.mapped_topic_id) if chunk.mapped_topic_id else None,
                    }
                )

        # Calculate prerequisite hash for idempotency
        hash_input = f"{payload.lecture_id}:{payload.curriculum_id}:{cov_summary_id}:{val_summary_id}:{len(transcript_chunks)}"
        prerequisite_hash = hashlib.md5(hash_input.encode("utf-8")).hexdigest()

        # Check existing active analysis
        existing_analysis = self.repo.get_active_analysis(payload.lecture_id)
        if existing_analysis and existing_analysis.prerequisite_hash == prerequisite_hash:
            logger.info("Prerequisites unchanged for lecture_id=%s. Returning existing analysis.", payload.lecture_id)
            existing_summary = self.repo.get_teaching_summary(payload.lecture_id)
            if existing_summary:
                return TeachingAnalyzeData(
                    lecture_id=str(payload.lecture_id),
                    teaching_score=existing_summary.overall_teaching_score,
                    grade=existing_summary.teaching_grade,
                    confidence=existing_summary.confidence_score,
                    explanation_score=existing_summary.explanation_score,
                    example_score=existing_summary.example_score,
                    structure_score=existing_summary.structure_score,
                    interaction_score=existing_summary.interaction_score,
                    coverage_score=existing_summary.coverage_score,
                    validation_score=existing_summary.validation_score,
                    strengths=existing_summary.strengths,
                    weaknesses=existing_summary.weaknesses,
                    analysis_reused=True,
                    qualitative_summary=existing_summary.qualitative_summary,
                )

        # Trigger re-computation
        trigger_reason = "PREREQUISITES_UPDATED" if existing_analysis else "INITIAL_ANALYSIS"
        self.repo.deactivate_previous_analyses(payload.lecture_id, trigger_reason=trigger_reason)

        # Run engines
        explanation_res = self.explanation_engine.analyze(transcript_chunks)
        logger.info("Explanation Analysis Completed: score=%.1f", explanation_res["score"])

        example_res = self.example_engine.analyze(transcript_chunks)
        logger.info("Example Detection Completed: count=%d, score=%.1f", example_res["example_count"], example_res["score"])

        structure_res = self.structure_engine.analyze(transcript_chunks)
        logger.info("Structure Analysis Completed: score=%.1f", structure_res["score"])

        interaction_res = self.interaction_engine.analyze(transcript_chunks)
        logger.info("Interaction Analysis Completed: score=%.1f", interaction_res["score"])

        # Fetch score weights from DB
        weights = self.repo.get_active_score_weights()

        coverage_score = coverage_summary.weighted_coverage_percentage if coverage_summary else 85.0
        validation_score = 90.0
        if validation_summary and hasattr(validation_summary, "validation_score"):
            validation_score = float(validation_summary.validation_score)

        overall_score, grade = self.scoring_engine.calculate_overall_score(
            explanation_score=explanation_res["score"],
            example_score=example_res["score"],
            structure_score=structure_res["score"],
            interaction_score=interaction_res["score"],
            coverage_score=coverage_score,
            validation_score=validation_score,
            weights=weights,
        )
        logger.info("Teaching Score Generated: overall=%.1f, grade=%s", overall_score, grade)

        confidence = self.scoring_engine.calculate_confidence(
            has_transcript=bool(transcript_chunks),
            has_coverage=bool(coverage_summary),
            has_validation=bool(validation_summary),
        )

        strengths, weaknesses = self.scoring_engine.consolidate_strengths_weaknesses(
            explanation_res, example_res, structure_res, interaction_res
        )

        # Construct DB entities
        analysis_orm = TeachingAnalysis(
            lecture_id=payload.lecture_id,
            curriculum_id=payload.curriculum_id,
            coverage_summary_id=cov_summary_id,
            validation_summary_id=val_summary_id,
            faculty_id=payload.faculty_id,
            prerequisite_hash=prerequisite_hash,
            is_active=True,
            regeneration_trigger=trigger_reason,
        )

        summary_orm = TeachingSummary(
            lecture_id=payload.lecture_id,
            overall_teaching_score=overall_score,
            teaching_grade=grade,
            confidence_score=confidence,
            explanation_score=explanation_res["score"],
            example_score=example_res["score"],
            structure_score=structure_res["score"],
            interaction_score=interaction_res["score"],
            coverage_score=coverage_score,
            validation_score=validation_score,
            strengths=strengths,
            weaknesses=weaknesses,
            qualitative_summary=explanation_res.get("qualitative_summary"),
            analysis_reused=False,
        )

        explanation_orm = TeachingExplanation(
            lecture_id=payload.lecture_id,
            score=explanation_res["score"],
            definition_quality=explanation_res["definition_quality"],
            concept_completeness=explanation_res["concept_completeness"],
            logical_progression=explanation_res["logical_progression"],
            step_by_step_clarity=explanation_res["step_by_step_clarity"],
            coherence_score=explanation_res["coherence_score"],
            redundancy_score=explanation_res["redundancy_score"],
            strengths=explanation_res["strengths"],
            weaknesses=explanation_res["weaknesses"],
        )

        examples_orm: List[TeachingExample] = []
        for ex in example_res["examples"]:
            topic_uuid = UUID(ex["topic_id"]) if ex.get("topic_id") else None
            examples_orm.append(
                TeachingExample(
                    lecture_id=payload.lecture_id,
                    topic_id=topic_uuid,
                    example_type=ex["example_type"],
                    description=ex["description"],
                    relevance_score=ex["relevance_score"],
                    quality_score=ex["quality_score"],
                    timestamp_start=ex["timestamp_start"],
                    timestamp_end=ex["timestamp_end"],
                )
            )

        structure_orm = TeachingStructure(
            lecture_id=payload.lecture_id,
            score=structure_res["score"],
            has_introduction=structure_res["has_introduction"],
            has_conclusion=structure_res["has_conclusion"],
            topic_jump_count=structure_res["topic_jump_count"],
            improper_ordering_count=structure_res["improper_ordering_count"],
            missing_transitions_count=structure_res["missing_transitions_count"],
            continuity_score=structure_res["continuity_score"],
            detected_flow=structure_res["detected_flow"],
        )

        interaction_orm = TeachingInteraction(
            lecture_id=payload.lecture_id,
            score=interaction_res["score"],
            faculty_question_count=interaction_res["faculty_question_count"],
            student_question_count=interaction_res["student_question_count"],
            faculty_answer_count=interaction_res["faculty_answer_count"],
            student_response_count=interaction_res["student_response_count"],
            interaction_density=interaction_res["interaction_density"],
            engagement_opportunities=interaction_res["engagement_opportunities"],
            clarification_requests=interaction_res["clarification_requests"],
            recap_questions=interaction_res["recap_questions"],
        )

        self.repo.create_teaching_record(
            analysis=analysis_orm,
            summary=summary_orm,
            explanation=explanation_orm,
            examples=examples_orm,
            structure=structure_orm,
            interaction=interaction_orm,
        )

        logger.info("Database Saved for Teaching Analysis id=%s", analysis_orm.id)

        return TeachingAnalyzeData(
            lecture_id=str(payload.lecture_id),
            teaching_score=overall_score,
            grade=grade,
            confidence=confidence,
            explanation_score=explanation_res["score"],
            example_score=example_res["score"],
            structure_score=structure_res["score"],
            interaction_score=interaction_res["score"],
            coverage_score=coverage_score,
            validation_score=validation_score,
            strengths=strengths,
            weaknesses=weaknesses,
            analysis_reused=False,
            qualitative_summary=explanation_res.get("qualitative_summary"),
        )

    # ── API Data Retrieval Methods ────────────────────────────────────────────

    def get_full_analysis(self, lecture_id: UUID) -> TeachingAnalyzeData:
        summary = self.repo.get_teaching_summary(lecture_id)
        if not summary:
            raise ValueError(f"No active teaching analysis found for lecture_id {lecture_id}")
        return TeachingAnalyzeData(
            lecture_id=str(lecture_id),
            teaching_score=summary.overall_teaching_score,
            grade=summary.teaching_grade,
            confidence=summary.confidence_score,
            explanation_score=summary.explanation_score,
            example_score=summary.example_score,
            structure_score=summary.structure_score,
            interaction_score=summary.interaction_score,
            coverage_score=summary.coverage_score,
            validation_score=summary.validation_score,
            strengths=summary.strengths,
            weaknesses=summary.weaknesses,
            analysis_reused=summary.analysis_reused,
            qualitative_summary=summary.qualitative_summary,
        )

    def get_summary(self, lecture_id: UUID) -> TeachingSummaryResponse:
        summary = self.repo.get_teaching_summary(lecture_id)
        if not summary:
            raise ValueError(f"No active teaching analysis found for lecture_id {lecture_id}")
        return TeachingSummaryResponse(
            lecture_id=str(lecture_id),
            teaching_score=summary.overall_teaching_score,
            grade=summary.teaching_grade,
            confidence=summary.confidence_score,
            qualitative_summary=summary.qualitative_summary,
        )

    def get_strengths(self, lecture_id: UUID) -> TeachingStrengthsResponse:
        summary = self.repo.get_teaching_summary(lecture_id)
        if not summary:
            raise ValueError(f"No active teaching analysis found for lecture_id {lecture_id}")
        return TeachingStrengthsResponse(lecture_id=str(lecture_id), strengths=summary.strengths)

    def get_weaknesses(self, lecture_id: UUID) -> TeachingWeaknessesResponse:
        summary = self.repo.get_teaching_summary(lecture_id)
        if not summary:
            raise ValueError(f"No active teaching analysis found for lecture_id {lecture_id}")
        return TeachingWeaknessesResponse(lecture_id=str(lecture_id), weaknesses=summary.weaknesses)

    def get_examples(self, lecture_id: UUID) -> TeachingExamplesResponse:
        examples = self.repo.get_teaching_examples(lecture_id)
        items = [
            TeachingExampleItem(
                example_id=str(ex.id),
                example_type=ex.example_type,
                description=ex.description,
                relevance_score=ex.relevance_score,
                quality_score=ex.quality_score,
                timestamp_start=ex.timestamp_start,
                timestamp_end=ex.timestamp_end,
                topic_id=str(ex.topic_id) if ex.topic_id else None,
            )
            for ex in examples
        ]
        return TeachingExamplesResponse(
            lecture_id=str(lecture_id), example_count=len(items), examples=items
        )

    def get_interaction(self, lecture_id: UUID) -> TeachingInteractionResponse:
        interaction = self.repo.get_teaching_interaction(lecture_id)
        if not interaction:
            raise ValueError(f"No active teaching interaction analysis found for lecture_id {lecture_id}")
        return TeachingInteractionResponse(
            lecture_id=str(lecture_id),
            interaction_score=interaction.score,
            faculty_question_count=interaction.faculty_question_count,
            student_question_count=interaction.student_question_count,
            faculty_answer_count=interaction.faculty_answer_count,
            student_response_count=interaction.student_response_count,
            interaction_density=interaction.interaction_density,
            engagement_opportunities=interaction.engagement_opportunities,
            clarification_requests=interaction.clarification_requests,
            recap_questions=interaction.recap_questions,
        )

    def get_structure(self, lecture_id: UUID) -> TeachingStructureResponse:
        structure = self.repo.get_teaching_structure(lecture_id)
        if not structure:
            raise ValueError(f"No active teaching structure analysis found for lecture_id {lecture_id}")
        return TeachingStructureResponse(
            lecture_id=str(lecture_id),
            structure_score=structure.score,
            has_introduction=structure.has_introduction,
            has_conclusion=structure.has_conclusion,
            topic_jump_count=structure.topic_jump_count,
            improper_ordering_count=structure.improper_ordering_count,
            missing_transitions_count=structure.missing_transitions_count,
            continuity_score=structure.continuity_score,
            detected_flow=structure.detected_flow,
        )

    def _ensure_parent_records(
        self, lecture_id: UUID, curriculum_id: UUID, faculty_id: Optional[UUID]
    ) -> None:
        """Create parent stub records in PostgreSQL if absent so foreign keys are satisfied."""
        from datetime import date
        from app.models.academic_term import AcademicTerm
        from app.models.course import Course
        from app.models.curriculum import Curriculum
        from app.models.department import Department
        from app.models.faculty import Faculty
        from app.models.institution import Institution
        from app.models.lecture_session import LectureSession
        from app.models.user import User

        inst = self.db.execute(select(Institution)).scalars().first()
        if not inst:
            inst = Institution(name="Default Institution", contact_email=f"def_{str(lecture_id)[:6]}@sample.edu")
            self.db.add(inst)
            self.db.flush()

        dept = self.db.execute(select(Department)).scalars().first()
        if not dept:
            dept = Department(institution_id=inst.id, name="Computer Science", code=f"CS_{str(lecture_id)[:6]}")
            self.db.add(dept)
            self.db.flush()

        usr = self.db.execute(select(User)).scalars().first()
        if not usr:
            usr = User(email=f"faculty_{str(lecture_id)[:6]}@example.com", full_name="Faculty User", password_hash="pw", role="FACULTY")
            self.db.add(usr)
            self.db.flush()

        fac = self.db.get(Faculty, faculty_id) if faculty_id else None
        if not fac:
            fac = self.db.execute(select(Faculty)).scalars().first()
            if not fac:
                fac = Faculty(user_id=usr.id, department_id=dept.id, employee_id="EMP001")
                self.db.add(fac)
                self.db.flush()

        course = self.db.execute(select(Course)).scalars().first()
        if not course:
            course = Course(department_id=dept.id, course_code="CS101", course_name="Intro to CS", credits=3)
            self.db.add(course)
            self.db.flush()

        term = self.db.execute(select(AcademicTerm)).scalars().first()
        if not term:
            term = AcademicTerm(
                institution_id=inst.id,
                academic_year="2025-2026",
                semester="1",
                start_date=date(2025, 9, 1),
                end_date=date(2025, 12, 31),
            )
            self.db.add(term)
            self.db.flush()

        curr = self.db.get(Curriculum, curriculum_id)
        if not curr:
            curr = Curriculum(
                id=curriculum_id,
                course_id=course.id,
                academic_term_id=term.id,
                faculty_id=fac.id,
                title="Sample Curriculum",
                document_type="SYLLABUS",
                file_name="syllabus.pdf",
                file_path="/tmp/syllabus.pdf",
                file_size=1024,
                mime_type="application/pdf",
                syllabus_version=f"v{str(curriculum_id)[:8]}",
            )
            self.db.add(curr)
            self.db.flush()

        lec = self.db.get(LectureSession, lecture_id)
        if not lec:
            lec = LectureSession(
                id=lecture_id,
                course_id=course.id,
                faculty_id=fac.id,
                lecture_date=date(2025, 10, 1),
                duration_minutes=60,
            )
            self.db.add(lec)
            self.db.flush()
