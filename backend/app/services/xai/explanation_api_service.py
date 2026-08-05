"""Thin service facade for the XAI REST API layer.

This service stays intentionally thin and delegates database work to the
existing repository and service stack already implemented for the Explainable AI
backend. It shapes repository data into the API-friendly structures expected by
Frontend consumers while preserving the existing clean architecture.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Iterable, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.exceptions.xai_exceptions import DuplicateExplanationError, ExplanationNotFoundError
from app.models.coverage_summary import CoverageSummary
from app.models.lecture_session import LectureSession
from app.repositories.xai.citation_repository import CitationRepository
from app.repositories.xai.confidence_repository import ConfidenceRepository
from app.repositories.xai.evidence_repository import EvidenceRepository
from app.repositories.xai.explanation_repository import ExplanationRepository
from app.repositories.xai.reasoning_repository import ReasoningRepository
from app.repositories.xai.summary_repository import SummaryRepository
from app.schemas.pagination import make_pagination_meta
from app.services.xai.evidence_collector import EvidenceCollectorService
from app.services.xai.explanation_builder_service import ExplanationBuilderService
from app.services.xai.summary_service import SummaryService

logger = logging.getLogger(__name__)


class ExplanationApiService:
    """Facade for REST API retrieval and generation of explainability data."""

    def __init__(self, db: Session):
        self.db = db
        self._explanation_repo = ExplanationRepository(db)
        self._evidence_repo = EvidenceRepository(db)
        self._citation_repo = CitationRepository(db)
        self._confidence_repo = ConfidenceRepository(db)
        self._reasoning_repo = ReasoningRepository(db)
        self._summary_repo = SummaryRepository(db)
        self._collector = EvidenceCollectorService(db)
        self._builder = ExplanationBuilderService(db)
        self._summary_svc = SummaryService(db)

    def generate(self, lecture_id: UUID) -> dict:
        """Generate and persist a complete explainability package for a lecture."""
        lecture = self.db.get(LectureSession, lecture_id)
        if lecture is None or lecture.status != "ACTIVE":
            raise ExplanationNotFoundError(str(lecture_id), "Lecture session not found")

        if self._explanation_repo.count_active_for_lecture(lecture_id) > 0:
            raise DuplicateExplanationError("explanation", "generate")

        start = time.perf_counter()
        bundle = self._collector.collect(lecture_id)
        curriculum_id = self._resolve_curriculum_id(lecture_id)
        records = self._builder.build_all(bundle, faculty_id=lecture.faculty_id, curriculum_id=curriculum_id)
        processing_time = round(time.perf_counter() - start, 3)
        summary = self._summary_svc.compute_and_save(lecture_id, records, processing_time=processing_time)
        self.db.commit()

        package = self._serialize_package(lecture_id, records, summary)
        logger.info("Explainability package generated — lecture_id=%s, total=%d", lecture_id, len(records))
        return package

    def get_package(self, lecture_id: UUID) -> dict:
        """Return the complete explainability package for a lecture."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        summary = self._summary_svc.get_summary(lecture_id)
        return self._serialize_package(lecture_id, records, summary)

    def get_summary(self, lecture_id: UUID) -> dict:
        """Return lecture-level explainability summary."""
        summary = self._summary_repo.get_by_lecture(lecture_id)
        if summary is None:
            raise ExplanationNotFoundError(str(lecture_id), "No explainability package found for this lecture")

        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        decision_counts: dict[str, int] = {}
        for record in records:
            decision_counts[record.decision_type] = decision_counts.get(record.decision_type, 0) + 1

        return {
            "lecture_id": str(lecture_id),
            "total_explanations": summary.total_explanations,
            "average_confidence": summary.average_confidence,
            "highest_confidence": summary.highest_confidence,
            "lowest_confidence": summary.lowest_confidence,
            "processing_time": summary.processing_time,
            "decision_counts": decision_counts,
        }

    def get_evidence(self, lecture_id: UUID, page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        """Return paginated evidence items for a lecture."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        items: List[dict] = []
        for record in records:
            for evidence_item in record.evidence_items:
                items.append(self._serialize_evidence_item(record, evidence_item))
        return self._paginate(items, page, page_size, sort, order, search)

    def get_transcripts(self, lecture_id: UUID, page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        """Return paginated transcript snippets only."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        items: List[dict] = []
        for record in records:
            for evidence_item in record.evidence_items:
                if evidence_item.transcript_evidence:
                    items.append(
                        {
                            "explanation_id": str(record.id),
                            "decision_id": str(record.decision_id),
                            "decision_type": record.decision_type,
                            "chunk_id": evidence_item.transcript_evidence.chunk_id,
                            "speaker": evidence_item.transcript_evidence.speaker,
                            "snippet": evidence_item.transcript_evidence.snippet,
                            "start_time": evidence_item.transcript_evidence.start_time,
                            "end_time": evidence_item.transcript_evidence.end_time,
                            "topic": self._infer_topic(record, evidence_item),
                        }
                    )
        return self._paginate(items, page, page_size, sort, order, search)

    def get_citations(self, lecture_id: UUID, page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        """Return paginated academic citations for lecture explainability."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        items: List[dict] = []
        for record in records:
            for evidence_item in record.evidence_items:
                if evidence_item.reference_citation:
                    items.append(
                        {
                            "explanation_id": str(record.id),
                            "decision_id": str(record.decision_id),
                            "decision_type": record.decision_type,
                            "book": evidence_item.reference_citation.document_name,
                            "notes": evidence_item.reference_citation.excerpt,
                            "reference_material": str(evidence_item.reference_citation.reference_material_id),
                            "curriculum": str(record.curriculum_id),
                            "chapter": evidence_item.reference_citation.chapter,
                            "section": evidence_item.reference_citation.section,
                            "excerpt": evidence_item.reference_citation.excerpt,
                        }
                    )
        return self._paginate(items, page, page_size, sort, order, search)

    def get_confidence(self, lecture_id: UUID, page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        """Return confidence calculations for lecture explainability."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        items: List[dict] = []
        for record in records:
            breakdown = record.confidence_breakdown
            items.append(
                {
                    "decision_id": str(record.decision_id),
                    "decision_type": record.decision_type,
                    "decision_source": record.decision_source,
                    "topic_match": breakdown.topic_match_score if breakdown else 0.0,
                    "coverage": breakdown.coverage_score if breakdown else 0.0,
                    "validation": breakdown.validation_score if breakdown else 0.0,
                    "reference": breakdown.reference_score if breakdown else 0.0,
                    "teaching": breakdown.teaching_score if breakdown else 0.0,
                    "recommendation": breakdown.recommendation_score if breakdown else 0.0,
                    "overall": breakdown.overall_confidence if breakdown else record.overall_confidence,
                }
            )
        return self._paginate(items, page, page_size, sort, order, search)

    def get_reasoning(self, lecture_id: UUID, page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        """Return reasoning graph for lecture explainability."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        items: List[dict] = []
        for record in records:
            for step in record.reasoning_steps:
                items.append(
                    {
                        "decision_id": str(record.decision_id),
                        "decision_type": record.decision_type,
                        "step_order": step.step_order,
                        "reason": step.reason,
                        "evidence_reference": step.evidence_reference,
                    }
                )
        return self._paginate(items, page, page_size, sort, order, search)

    def get_timeline(self, lecture_id: UUID, page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        """Return chronological explanation timeline entries."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        items: List[dict] = []
        for record in records:
            for evidence_item in record.evidence_items:
                snippet = evidence_item.transcript_evidence
                if snippet is None:
                    continue
                items.append(
                    {
                        "decision_id": str(record.decision_id),
                        "decision_type": record.decision_type,
                        "start_time": snippet.start_time,
                        "end_time": snippet.end_time,
                        "speaker": snippet.speaker,
                        "snippet": snippet.snippet,
                        "topic": self._infer_topic(record, evidence_item),
                    }
                )
        return self._paginate(items, page, page_size, sort, order, search)

    def get_decision(self, lecture_id: UUID, decision_id: UUID) -> dict:
        """Return explainability package for single AI decision."""
        records = self._explanation_repo.get_all_active_for_lecture(lecture_id)
        for record in records:
            if str(record.decision_id) == str(decision_id):
                return self._serialize_record(record)
        raise ExplanationNotFoundError(str(decision_id), "Decision explanation not found")

    def _serialize_package(self, lecture_id: UUID, records: List[Any], summary: dict) -> dict:
        decisions = [self._serialize_record(record) for record in records]
        overall_confidence = round(sum(r.overall_confidence for r in records) / len(records), 2) if records else 0.0
        return {
            "lecture_id": str(lecture_id),
            "overall_confidence": overall_confidence,
            "decision_count": len(records),
            "summary": summary,
            "decisions": decisions,
        }

    def _serialize_record(self, record: Any) -> dict:
        evidence_item = record.evidence_items[0] if record.evidence_items else None
        transcript = evidence_item.transcript_evidence if evidence_item else None
        citation = evidence_item.reference_citation if evidence_item else None
        breakdown = record.confidence_breakdown
        reasoning_steps = [
            {
                "step_order": step.step_order,
                "reason": step.reason,
                "evidence_reference": step.evidence_reference,
            }
            for step in record.reasoning_steps
        ]

        return {
            "decision_id": str(record.decision_id),
            "decision_type": record.decision_type,
            "decision_source": record.decision_source,
            "reason": self._decision_reason(record),
            "transcript": {
                "snippet": transcript.snippet if transcript else None,
                "start_time": transcript.start_time if transcript else 0.0,
                "end_time": transcript.end_time if transcript else 0.0,
            },
            "citation": {
                "document": citation.document_name if citation else None,
                "chapter": citation.chapter if citation else None,
                "section": citation.section if citation else None,
                "excerpt": citation.excerpt if citation else None,
            },
            "confidence": {
                "overall": breakdown.overall_confidence if breakdown else record.overall_confidence,
                "breakdown": {
                    "topic_match": breakdown.topic_match_score if breakdown else 0.0,
                    "coverage": breakdown.coverage_score if breakdown else 0.0,
                    "validation": breakdown.validation_score if breakdown else 0.0,
                    "reference": breakdown.reference_score if breakdown else 0.0,
                    "teaching": breakdown.teaching_score if breakdown else 0.0,
                    "recommendation": breakdown.recommendation_score if breakdown else 0.0,
                },
            },
            "reasoning": reasoning_steps,
        }

    def _serialize_evidence_item(self, record: Any, evidence_item: Any) -> dict:
        citation = evidence_item.reference_citation
        transcript = evidence_item.transcript_evidence
        return {
            "explanation_id": str(record.id),
            "decision_id": str(record.decision_id),
            "decision_type": record.decision_type,
            "evidence_type": evidence_item.evidence_type,
            "importance_score": evidence_item.importance_score,
            "coverage_result_id": str(evidence_item.coverage_result_id) if evidence_item.coverage_result_id else None,
            "validation_result_id": str(evidence_item.validation_result_id) if evidence_item.validation_result_id else None,
            "teaching_analysis_id": str(evidence_item.teaching_analysis_id) if evidence_item.teaching_analysis_id else None,
            "recommendation_id": str(evidence_item.recommendation_id) if evidence_item.recommendation_id else None,
            "transcript": {
                "chunk_id": transcript.chunk_id if transcript else None,
                "speaker": transcript.speaker if transcript else None,
                "snippet": transcript.snippet if transcript else None,
                "start_time": transcript.start_time if transcript else 0.0,
                "end_time": transcript.end_time if transcript else 0.0,
            },
            "citation": {
                "document": citation.document_name if citation else None,
                "chapter": citation.chapter if citation else None,
                "section": citation.section if citation else None,
                "excerpt": citation.excerpt if citation else None,
                "reference_material_id": str(citation.reference_material_id) if citation else None,
            },
        }

    def _decision_reason(self, record: Any) -> str:
        for step in record.reasoning_steps:
            if "[CONCLUSION]" in step.reason:
                return step.reason.replace("[CONCLUSION]", "").strip()
        return record.explanation_summary

    def _infer_topic(self, record: Any, evidence_item: Any) -> str:
        if evidence_item.coverage_result and evidence_item.coverage_result.topic_name:
            return evidence_item.coverage_result.topic_name
        if evidence_item.validation_result and evidence_item.validation_result.validation_status:
            return evidence_item.validation_result.validation_status
        if record.decision_type:
            return record.decision_type
        return "Unknown"

    def _resolve_curriculum_id(self, lecture_id: UUID) -> Optional[UUID]:
        summary = (
            self.db.query(CoverageSummary)
            .filter(CoverageSummary.lecture_id == lecture_id, CoverageSummary.status == "ACTIVE")
            .first()
        )
        return summary.curriculum_id if summary else None

    def _paginate(self, items: List[dict], page: int, page_size: int, sort: str, order: str, search: Optional[str]) -> dict:
        filtered = items
        if search:
            needle = search.strip().lower()
            filtered = [
                item for item in items
                if any(str(value).lower().find(needle) >= 0 for value in item.values())
            ]

        if sort:
            reverse = order.lower() == "desc"
            filtered = sorted(filtered, key=lambda item: item.get(sort, ""), reverse=reverse)

        total_items = len(filtered)
        total_pages = max(1, (total_items + page_size - 1) // page_size) if total_items else 1
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = filtered[start:end]

        return {
            "items": paged_items,
            "pagination": make_pagination_meta(page, page_size, total_items),
            "total_items": total_items,
            "total_pages": total_pages,
        }
