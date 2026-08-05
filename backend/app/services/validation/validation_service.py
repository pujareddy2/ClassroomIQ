"""
Main Technical Validation Engine Service.
Orchestrates reference retrieval, modular validators (Formula, Code, Terminology, Concept),
confidence scoring, DB persistence, quality score calculation, and timeline generation.
"""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.curriculum import Curriculum
from app.models.lecture_session import LectureSession
from app.models.topic import Topic
from app.models.validation_evidence import ValidationEvidence
from app.models.validation_result import ValidationResult
from app.models.validation_summary import ValidationSummary
from app.services.validation.confidence_calculator import ConfidenceCalculator
from app.services.validation.exceptions import (
    CurriculumNotFoundError,
    EmptyTranscriptError,
    LectureNotFoundError,
)
from app.services.validation.reference_retriever import ReferenceRetriever
from app.services.validation.validation_models import (
    InternalEvidence,
    SeverityLevel,
    ValidationCategory,
    ValidationChunkResult,
    ValidationStatus,
    ValidationType,
)
from app.services.validation.validators import (
    CodeValidator,
    ConceptValidator,
    FormulaValidator,
    TerminologyValidator,
)

logger = logging.getLogger(__name__)


class ValidationService:
    """Orchestrator for the Technical Validation Engine."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.reference_retriever = ReferenceRetriever(db)
        self.concept_validator = ConceptValidator()

    def process_and_validate_transcript(
        self,
        transcript_chunks: List[Dict[str, Any]],
        lecture_id: Optional[UUID] = None,
        curriculum_id: Optional[UUID] = None,
        course_id: Optional[str] = None,
        faculty_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Main pipeline entry point:
        Analyses structured transcript chunks (received with topic_id) and validates technical accuracy.
        """
        start_time = perf_counter()
        logger.info("Validation Started: Processing %d transcript chunk(s)", len(transcript_chunks))

        if not transcript_chunks:
            logger.error("Empty Transcript: No chunks provided for validation")
            raise EmptyTranscriptError("Transcript chunk list cannot be empty")

        # ── 1. Resolve Curriculum ─────────────────────────────────────────────
        if not curriculum_id:
            first_topic = self.db.query(Topic).first()
            if first_topic:
                curriculum_id = first_topic.curriculum_id
            else:
                first_curr = self.db.query(Curriculum).first()
                if not first_curr:
                    logger.error("No curriculum found in database")
                    raise CurriculumNotFoundError("No curriculum found in database for validation")
                curriculum_id = first_curr.id

        logger.info("Curriculum Loaded: ID %s", curriculum_id)

        # ── 2. Resolve / Create LectureSession ────────────────────────────────
        if not lecture_id:
            curriculum = self.db.get(Curriculum, curriculum_id)
            c_id = curriculum.course_id if curriculum else None
            f_id = faculty_id or (curriculum.faculty_id if curriculum else None)

            if not c_id or not f_id:
                lec = self.db.query(LectureSession).first()
                if lec:
                    lecture_id = lec.id
                    c_id = lec.course_id
                    f_id = lec.faculty_id

            if not lecture_id:
                new_lec = LectureSession(
                    id=uuid4(),
                    course_id=c_id,
                    faculty_id=f_id,
                    lecture_date=self.db.query(Curriculum).first().uploaded_at.date() if self.db.query(Curriculum).first() else None,
                    duration_minutes=60,
                    classroom="Virtual / Recorded",
                )
                self.db.add(new_lec)
                self.db.flush()
                lecture_id = new_lec.id

        # ── 3. Validate Each Chunk with Modular Validators ────────────────────
        chunk_results: List[ValidationChunkResult] = []

        for c_data in transcript_chunks:
            c_id_str = str(c_data.get("chunk_id", uuid4()))
            text = c_data.get("text", "").strip()
            start_t = float(c_data.get("start_time", 0.0))
            end_t = float(c_data.get("end_time", 0.0))
            speaker = c_data.get("speaker", "Faculty")

            # Receive topic_id directly from Coverage Engine / Member 1 payload
            raw_topic_id = c_data.get("topic_id")
            topic_id = UUID(str(raw_topic_id)) if raw_topic_id else None
            topic_name = "General"

            if topic_id:
                topic_obj = self.db.get(Topic, topic_id)
                if topic_obj:
                    topic_name = topic_obj.topic_name

            if not text:
                continue

            # Retrieve references for topic
            references = self.reference_retriever.retrieve_references_for_topic(
                curriculum_id, topic_id, topic_name
            )
            ref_texts = [r[3] for r in references]
            combined_ref_text = " ".join(ref_texts)

            # a. Formula Validator
            formula_res = FormulaValidator.validate(text, combined_ref_text)
            if formula_res:
                cat, status, v_type, s_level, reason, raw_score = formula_res
                conf_score, conf_level = ConfidenceCalculator.calculate(
                    0.90 if topic_id else 0.50, len(references), raw_score
                )
                evidence = [
                    InternalEvidence(
                        reference_material_id=references[0][0] if references else None,
                        reference_document=references[0][1] if references else "Academic Math Reference",
                        reference_section=references[0][2] if references else "Mathematical Models",
                        reference_excerpt=text,
                        curriculum_topic=topic_name,
                        explanation=reason,
                    )
                ]
                chunk_results.append(
                    ValidationChunkResult(
                        chunk_id=c_id_str,
                        chunk_text=text,
                        chunk_start_time=start_t,
                        chunk_end_time=end_t,
                        speaker=speaker,
                        topic_id=topic_id,
                        topic_name=topic_name,
                        category=cat,
                        status=status,
                        validation_type=v_type,
                        severity=s_level,
                        confidence_score=conf_score,
                        confidence_level=conf_level,
                        reason=reason,
                        evidence=evidence,
                    )
                )
                logger.info("Chunk Validated: Formula issue in chunk %s", c_id_str)
                continue

            # b. Code Validator
            code_res = CodeValidator.validate(text, combined_ref_text)
            if code_res:
                cat, status, v_type, s_level, reason, raw_score = code_res
                conf_score, conf_level = ConfidenceCalculator.calculate(
                    0.90 if topic_id else 0.50, len(references), raw_score
                )
                evidence = [
                    InternalEvidence(
                        reference_material_id=references[0][0] if references else None,
                        reference_document=references[0][1] if references else "Programming Standard",
                        reference_section=references[0][2] if references else "Code Conventions",
                        reference_excerpt=text,
                        curriculum_topic=topic_name,
                        explanation=reason,
                    )
                ]
                chunk_results.append(
                    ValidationChunkResult(
                        chunk_id=c_id_str,
                        chunk_text=text,
                        chunk_start_time=start_t,
                        chunk_end_time=end_t,
                        speaker=speaker,
                        topic_id=topic_id,
                        topic_name=topic_name,
                        category=cat,
                        status=status,
                        validation_type=v_type,
                        severity=s_level,
                        confidence_score=conf_score,
                        confidence_level=conf_level,
                        reason=reason,
                        evidence=evidence,
                    )
                )
                logger.info("Chunk Validated: Code issue in chunk %s", c_id_str)
                continue

            # c. Terminology Validator
            term_res = TerminologyValidator.validate(text, combined_ref_text)
            if term_res:
                cat, status, v_type, s_level, reason, raw_score = term_res
                conf_score, conf_level = ConfidenceCalculator.calculate(
                    0.90 if topic_id else 0.50, len(references), raw_score
                )
                evidence = [
                    InternalEvidence(
                        reference_material_id=references[0][0] if references else None,
                        reference_document=references[0][1] if references else "Academic Glossary",
                        reference_section=references[0][2] if references else "Terminology",
                        reference_excerpt=text,
                        curriculum_topic=topic_name,
                        explanation=reason,
                    )
                ]
                chunk_results.append(
                    ValidationChunkResult(
                        chunk_id=c_id_str,
                        chunk_text=text,
                        chunk_start_time=start_t,
                        chunk_end_time=end_t,
                        speaker=speaker,
                        topic_id=topic_id,
                        topic_name=topic_name,
                        category=cat,
                        status=status,
                        validation_type=v_type,
                        severity=s_level,
                        confidence_score=conf_score,
                        confidence_level=conf_level,
                        reason=reason,
                        evidence=evidence,
                    )
                )
                logger.info("Chunk Validated: Terminology issue in chunk %s", c_id_str)
                continue

            # d. Concept Validator (LLM / Hybrid Concept Checking)
            cat, status, v_type, s_level, reason, raw_score = self.concept_validator.validate(
                text, topic_name, references
            )
            conf_score, conf_level = ConfidenceCalculator.calculate(
                0.90 if topic_id else 0.50, len(references), raw_score
            )
            evidence = [
                InternalEvidence(
                    reference_material_id=references[0][0] if references else None,
                    reference_document=references[0][1] if references else "Official Syllabus",
                    reference_section=references[0][2] if references else "Syllabus Content",
                    reference_excerpt=text,
                    curriculum_topic=topic_name,
                    explanation=reason,
                )
            ]
            chunk_results.append(
                ValidationChunkResult(
                    chunk_id=c_id_str,
                    chunk_text=text,
                    chunk_start_time=start_t,
                    chunk_end_time=end_t,
                    speaker=speaker,
                    topic_id=topic_id,
                    topic_name=topic_name,
                    category=cat,
                    status=status,
                    validation_type=v_type,
                    severity=s_level,
                    confidence_score=conf_score,
                    confidence_level=conf_level,
                    reason=reason,
                    evidence=evidence,
                )
            )
            logger.info("Chunk Validated: Result '%s' for chunk %s", status.value, c_id_str)

        # ── 4. Persist Results to PostgreSQL ─────────────────────────────────
        correct_count = 0
        incorrect_count = 0
        formula_count = 0
        code_count = 0
        missing_count = 0
        term_count = 0
        total_confidence = 0.0

        for r in chunk_results:
            total_confidence += r.confidence_score

            if r.status == ValidationStatus.CORRECT:
                correct_count += 1
            else:
                incorrect_count += 1

            if r.category == ValidationCategory.FORMULA:
                formula_count += 1
            elif r.category == ValidationCategory.CODE:
                code_count += 1
            elif r.category in (ValidationCategory.TERMINOLOGY, ValidationCategory.DEFINITION):
                term_count += 1
            elif r.status == ValidationStatus.MISSING:
                missing_count += 1

            val_res = ValidationResult(
                id=uuid4(),
                lecture_id=lecture_id,
                curriculum_id=curriculum_id,
                topic_id=r.topic_id,
                chunk_id=r.chunk_id,
                chunk_text=r.chunk_text,
                chunk_start_time=r.chunk_start_time,
                chunk_end_time=r.chunk_end_time,
                speaker=r.speaker,
                category=r.category.value,
                validation_status=r.status.value,
                validation_type=r.validation_type.value,
                severity=r.severity.value,
                confidence_score=r.confidence_score,
                confidence_level=r.confidence_level.value,
                reason=r.reason,
            )
            self.db.add(val_res)
            self.db.flush()

            for ev in r.evidence:
                val_ev = ValidationEvidence(
                    id=uuid4(),
                    validation_result_id=val_res.id,
                    reference_material_id=ev.reference_material_id,
                    reference_document=ev.reference_document,
                    reference_section=ev.reference_section,
                    reference_excerpt=ev.reference_excerpt,
                    curriculum_topic=ev.curriculum_topic,
                    explanation=ev.explanation,
                )
                self.db.add(val_ev)

        # ── 5. Analytics & Quality Score Calculation ──────────────────────────
        total_chunks = len(chunk_results)
        val_pct = round((correct_count / float(total_chunks)) * 100.0, 1) if total_chunks > 0 else 100.0
        avg_conf = round(total_confidence / float(total_chunks), 1) if total_chunks > 0 else 0.0

        # overall_validation_score (0-100)
        overall_score = round(0.7 * val_pct + 0.3 * avg_conf, 1)

        if overall_score >= 90.0:
            quality = "EXCELLENT"
        elif overall_score >= 75.0:
            quality = "GOOD"
        elif overall_score >= 60.0:
            quality = "NEEDS_ATTENTION"
        else:
            quality = "POOR"

        elapsed_sec = round(perf_counter() - start_time, 2)

        # Upsert ValidationSummary
        existing_summary = self.db.query(ValidationSummary).filter(ValidationSummary.lecture_id == lecture_id).first()
        if existing_summary:
            existing_summary.validated_chunks = total_chunks
            existing_summary.correct_concepts = correct_count
            existing_summary.incorrect_concepts = incorrect_count
            existing_summary.formula_issues = formula_count
            existing_summary.code_issues = code_count
            existing_summary.missing_concepts = missing_count
            existing_summary.terminology_errors = term_count
            existing_summary.overall_validation_score = overall_score
            existing_summary.lecture_quality = quality
            existing_summary.validation_percentage = val_pct
            existing_summary.average_confidence = avg_conf
            existing_summary.processing_time_seconds = elapsed_sec
        else:
            summary = ValidationSummary(
                id=uuid4(),
                lecture_id=lecture_id,
                curriculum_id=curriculum_id,
                validated_chunks=total_chunks,
                correct_concepts=correct_count,
                incorrect_concepts=incorrect_count,
                formula_issues=formula_count,
                code_issues=code_count,
                missing_concepts=missing_count,
                terminology_errors=term_count,
                overall_validation_score=overall_score,
                lecture_quality=quality,
                validation_percentage=val_pct,
                average_confidence=avg_conf,
                processing_time_seconds=elapsed_sec,
            )
            self.db.add(summary)

        self.db.flush()
        logger.info("Validation Stored: Persisted %d result(s) in PostgreSQL", total_chunks)

        return {
            "status": "SUCCESS",
            "lecture_id": str(lecture_id),
            "validated_chunks": total_chunks,
            "correct_concepts": correct_count,
            "incorrect_concepts": incorrect_count,
            "formula_issues": formula_count,
            "code_issues": code_count,
            "missing_concepts": missing_count,
            "terminology_errors": term_count,
            "overall_validation_score": overall_score,
            "lecture_quality": quality,
            "validation_percentage": val_pct,
            "average_confidence": avg_conf,
        }

    # ── Retrieval API Methods ───────────────────────────────────────────────────

    def get_validation_results(self, lecture_id: UUID) -> List[Dict[str, Any]]:
        stmt = (
            select(ValidationResult)
            .where(ValidationResult.lecture_id == lecture_id)
            .order_by(ValidationResult.chunk_start_time.asc())
        )
        results = self.db.execute(stmt).scalars().all()
        if not results:
            raise LectureNotFoundError(f"No validation results found for lecture '{lecture_id}'")

        output = []
        for r in results:
            evidence_data = [
                {
                    "id": str(e.id),
                    "validation_result_id": str(e.validation_result_id),
                    "reference_document": e.reference_document,
                    "reference_section": e.reference_section,
                    "reference_excerpt": e.reference_excerpt,
                    "curriculum_topic": e.curriculum_topic,
                    "explanation": e.explanation,
                }
                for e in r.evidence_list
            ]
            output.append(
                {
                    "id": str(r.id),
                    "lecture_id": str(r.lecture_id),
                    "curriculum_id": str(r.curriculum_id),
                    "topic_id": str(r.topic_id) if r.topic_id else None,
                    "chunk_id": r.chunk_id,
                    "chunk_text": r.chunk_text,
                    "chunk_start_time": r.chunk_start_time,
                    "chunk_end_time": r.chunk_end_time,
                    "speaker": r.speaker or "Faculty",
                    "category": r.category or "CONCEPT",
                    "validation_status": r.validation_status or "CORRECT",
                    "validation_type": r.validation_type,
                    "severity": r.severity,
                    "confidence_score": r.confidence_score,
                    "confidence_level": r.confidence_level,
                    "reason": r.reason,
                    "evidence": evidence_data,
                }
            )
        return output

    def get_validation_summary(self, lecture_id: UUID) -> Dict[str, Any]:
        summary = self.db.query(ValidationSummary).filter(ValidationSummary.lecture_id == lecture_id).first()
        if not summary:
            raise LectureNotFoundError(f"No validation summary found for lecture '{lecture_id}'")

        results = self.db.query(ValidationResult).filter(ValidationResult.lecture_id == lecture_id).all()
        dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for r in results:
            dist[r.confidence_level] = dist.get(r.confidence_level, 0) + 1

        return {
            "lecture_id": str(summary.lecture_id),
            "curriculum_id": str(summary.curriculum_id),
            "validated_chunks": summary.validated_chunks,
            "correct_concepts": summary.correct_concepts,
            "incorrect_concepts": summary.incorrect_concepts,
            "formula_issues": summary.formula_issues,
            "code_issues": summary.code_issues,
            "missing_concepts": summary.missing_concepts,
            "terminology_errors": summary.terminology_errors,
            "overall_validation_score": summary.overall_validation_score,
            "lecture_quality": summary.lecture_quality,
            "validation_percentage": summary.validation_percentage,
            "average_confidence": summary.average_confidence,
            "confidence_distribution": dist,
        }

    def get_validation_evidence(self, lecture_id: UUID) -> List[Dict[str, Any]]:
        stmt = (
            select(ValidationEvidence)
            .join(ValidationResult, ValidationEvidence.validation_result_id == ValidationResult.id)
            .where(ValidationResult.lecture_id == lecture_id)
        )
        evidence_rows = self.db.execute(stmt).scalars().all()
        if not evidence_rows:
            raise LectureNotFoundError(f"No evidence records found for lecture '{lecture_id}'")

        return [
            {
                "id": str(e.id),
                "validation_result_id": str(e.validation_result_id),
                "reference_document": e.reference_document,
                "reference_section": e.reference_section,
                "reference_excerpt": e.reference_excerpt,
                "curriculum_topic": e.curriculum_topic,
                "explanation": e.explanation,
            }
            for e in evidence_rows
        ]

    def get_validation_timeline(self, lecture_id: UUID) -> Dict[str, Any]:
        """
        NEW: Returns chronological timeline intervals for frontend visualization.
        Allows UI video player to render red/green timeline bands.
        """
        stmt = (
            select(ValidationResult)
            .where(ValidationResult.lecture_id == lecture_id)
            .order_by(ValidationResult.chunk_start_time.asc())
        )
        results = self.db.execute(stmt).scalars().all()
        if not results:
            raise LectureNotFoundError(f"No validation records found for lecture '{lecture_id}'")

        intervals = []
        max_time = 0.0

        for r in results:
            if r.chunk_end_time > max_time:
                max_time = r.chunk_end_time

            snippet = r.chunk_text[:80] + "..." if len(r.chunk_text) > 80 else r.chunk_text
            intervals.append(
                {
                    "chunk_id": r.chunk_id,
                    "start_time": r.chunk_start_time,
                    "end_time": r.chunk_end_time,
                    "speaker": r.speaker or "Faculty",
                    "category": r.category or "CONCEPT",
                    "status": r.validation_status or "CORRECT",
                    "severity": r.severity,
                    "confidence_score": r.confidence_score,
                    "text_snippet": snippet,
                    "reason": r.reason,
                }
            )

        return {
            "status": "SUCCESS",
            "lecture_id": str(lecture_id),
            "total_duration_seconds": max_time,
            "intervals": intervals,
        }

    def get_high_severity_issues(self, lecture_id: UUID) -> list:
        """
        GET /api/v1/validation/{lecture_id}/issues
        Returns only HIGH severity validation results for quick triage by faculty.
        Includes: INCORRECT, FORMULA_ERROR, CODE_ERROR categories.
        """
        stmt = (
            select(ValidationResult)
            .where(
                ValidationResult.lecture_id == lecture_id,
                ValidationResult.severity.in_(["HIGH", "CRITICAL"]),
                ValidationResult.validation_status.in_(["INCORRECT", "FORMULA_ERROR", "CODE_ERROR"]),
            )
            .order_by(ValidationResult.chunk_start_time.asc())
        )
        results = self.db.execute(stmt).scalars().all()
        if not results:
            # Not an error — could be a perfect lecture
            return []

        issues = []
        for r in results:
            evidence_items = [
                {
                    "id": str(e.id),
                    "validation_result_id": str(r.id),
                    "reference_document": e.reference_document,
                    "reference_section": e.reference_section,
                    "reference_excerpt": e.reference_excerpt,
                    "curriculum_topic": e.curriculum_topic,
                    "explanation": e.explanation,
                }
                for e in self.db.query(ValidationEvidence)
                .filter(ValidationEvidence.validation_result_id == r.id)
                .all()
            ]
            issues.append(
                {
                    "id": str(r.id),
                    "chunk_id": r.chunk_id,
                    "chunk_text": r.chunk_text,
                    "chunk_start_time": r.chunk_start_time,
                    "chunk_end_time": r.chunk_end_time,
                    "category": r.category or "CONCEPT",
                    "validation_status": r.validation_status or "INCORRECT",
                    "severity": r.severity,
                    "confidence_score": r.confidence_score,
                    "reason": r.reason,
                    "evidence": evidence_items,
                }
            )
        return issues
