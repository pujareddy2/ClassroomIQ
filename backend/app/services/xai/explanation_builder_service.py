"""
ExplanationBuilderService

Master orchestrator that assembles one ExplanationRecord per upstream AI decision.

Pipeline per EvidenceCandidate:
  1. Check idempotency — skip if active explanation already exists for this decision
  2. Supersede existing if source decision changed
  3. Create EvidenceItem (FK → upstream result row)
  4. Attach TranscriptEvidence snippet
  5. Attach ReferenceCitation
  6. Compute ConfidenceBreakdown
  7. Generate ReasoningStep DAG
  8. Build ExplanationRecord with explanation_summary
  9. Persist atomically via repositories

Rules:
  - Only one ACTIVE explanation per decision.
  - Never duplicate upstream data — reference by FK only.
  - Log every step.
  - Per-candidate error isolation: one failure does not abort the batch.
"""

import logging
import time
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.explanation_engine import (
    ConfidenceBreakdown,
    EvidenceItem,
    ExplanationRecord,
    ReasoningStep,
    ReferenceCitation,
    TranscriptEvidence,
)
from app.repositories.xai.explanation_repository import ExplanationRepository
from app.services.xai.citation_service import CitationService
from app.services.xai.confidence_service import ConfidenceService
from app.services.xai.evidence_collector import CollectedEvidence, EvidenceCandidate
from app.services.xai.reasoning_service import ReasoningService
from app.services.xai.transcript_evidence_service import TranscriptEvidenceService

logger = logging.getLogger(__name__)


class ExplanationBuilderService:
    """
    Assembles complete ExplanationRecord packages from collected evidence.
    Manages idempotency, superseding, and atomic persistence.
    """

    def __init__(self, db: Session):
        self.db = db
        self._repo = ExplanationRepository(db)
        self._transcript_svc = TranscriptEvidenceService(db)
        self._citation_svc = CitationService(db)
        self._confidence_svc = ConfidenceService()
        self._reasoning_svc = ReasoningService()

    def build_all(
        self,
        bundle: CollectedEvidence,
        faculty_id: Optional[UUID] = None,
        curriculum_id: Optional[UUID] = None,
    ) -> List[ExplanationRecord]:
        """
        Build ExplanationRecords for all candidates in the bundle.
        Returns the list of persisted (or cached) records.
        """
        start = time.perf_counter()
        results: List[ExplanationRecord] = []

        for candidate in bundle.candidates:
            try:
                record = self._build_one(
                    lecture_id=bundle.lecture_id,
                    candidate=candidate,
                    faculty_id=faculty_id,
                    curriculum_id=curriculum_id,
                )
                results.append(record)
            except Exception as e:
                logger.error(
                    "Explanation build failed for [%s / %s]: %s",
                    candidate.source, candidate.decision_type, e,
                )
                # Per-candidate error isolation — never fail the entire batch

        elapsed = time.perf_counter() - start
        logger.info(
            "Explanation Built — lecture_id=%s, explanations=%d, time=%.3fs",
            bundle.lecture_id, len(results), elapsed,
        )
        return results

    def _build_one(
        self,
        lecture_id: UUID,
        candidate: EvidenceCandidate,
        faculty_id: Optional[UUID],
        curriculum_id: Optional[UUID],
    ) -> ExplanationRecord:
        """Build or return cached ExplanationRecord for a single decision."""

        # ── Idempotency check ────────────────────────────────────────────────
        existing = self._repo.get_active(
            lecture_id=lecture_id,
            decision_source=candidate.source,
            decision_type=candidate.decision_type,
            decision_id=candidate.decision_id,
        )
        if existing:
            logger.info(
                "Explanation reused (idempotent) — source=%s, type=%s",
                candidate.source, candidate.decision_type,
            )
            return existing

        # ── Supersede any previous ACTIVE explanation for this decision ───────
        superseded = self._repo.supersede_existing(
            lecture_id=lecture_id,
            decision_source=candidate.source,
            decision_type=candidate.decision_type,
            decision_id=candidate.decision_id,
        )
        if superseded > 0:
            logger.info("Superseded %d previous explanation(s)", superseded)

        # ── Build ReferenceCitation (pre-fetch to get citation confidence) ─────
        # Note: evidence_item_id will be linked after creation
        temp_ev_id = uuid4()
        citation = self._citation_svc.find_citation(
            evidence_item_id=temp_ev_id,
            topic_name=candidate.subject,
            curriculum_id=curriculum_id,
        )
        logger.info("Reference Citation Loaded — doc=%s", citation.document_name)

        # ── Compute Confidence ────────────────────────────────────────────────
        conf_result = self._confidence_svc.calculate(
            candidate=candidate,
            citation_confidence=citation.citation_confidence,
        )
        logger.info("Confidence Calculated — overall=%.2f", conf_result.overall_confidence)

        # ── Generate Reasoning Steps ──────────────────────────────────────────
        reasoning_data = self._reasoning_svc.build_steps(
            candidate=candidate,
            citation_doc_name=citation.document_name,
        )
        logger.info("Reasoning Generated — %d steps", len(reasoning_data))

        # ── Build explanation summary text ────────────────────────────────────
        conclusion = next(
            (s.reason for s in reasoning_data if "[CONCLUSION]" in s.reason), ""
        )
        summary_text = conclusion or f"{candidate.source}: {candidate.description}"

        # ── Assemble ExplanationRecord ────────────────────────────────────────
        record = ExplanationRecord(
            lecture_id=lecture_id,
            faculty_id=faculty_id,
            curriculum_id=curriculum_id,
            decision_source=candidate.source,
            decision_type=candidate.decision_type,
            decision_id=candidate.decision_id,
            overall_confidence=conf_result.overall_confidence,
            explanation_summary=summary_text,
            status="ACTIVE",
        )
        self.db.add(record)
        self.db.flush()  # Assigns record.id

        # ── Build EvidenceItem ────────────────────────────────────────────────
        evidence_item = self._create_evidence_item(candidate)
        evidence_item.explanation_record_id = record.id
        self.db.add(evidence_item)
        self.db.flush()  # Assigns evidence_item.id

        # ── Build TranscriptEvidence snippet ──────────────────────────────────
        chunk_id = None
        if candidate.source == "validation":
            chunk_id = None
        transcript_ev = self._transcript_svc.find_snippet(
            evidence_item_id=evidence_item.id,
            lecture_id=lecture_id,
            chunk_id=chunk_id,
            topic_name=candidate.subject,
        )
        transcript_ev.evidence_item_id = evidence_item.id
        self.db.add(transcript_ev)
        logger.info("Transcript Evidence Generated — evidence_item=%s", evidence_item.id)

        # ── Attach ReferenceCitation ──────────────────────────────────────────
        citation.evidence_item_id = evidence_item.id
        self.db.add(citation)

        # ── Attach confidence breakdown ───────────────────────────────────────
        conf_orm = self._confidence_svc.to_orm(record.id, conf_result)
        self.db.add(conf_orm)

        # ── Attach reasoning steps ────────────────────────────────────────────
        step_orms = self._reasoning_svc.to_orm_list(record.id, reasoning_data)
        for step in step_orms:
            self.db.add(step)

        self.db.flush()

        logger.info("Database Saved — explanation_record_id=%s", record.id)
        return record

    def _create_evidence_item(self, candidate: EvidenceCandidate) -> EvidenceItem:
        """Create an EvidenceItem with the correct upstream FK populated."""
        item = EvidenceItem(
            evidence_type=candidate.source,
            importance_score=self._compute_importance(candidate),
        )

        # Populate exactly one upstream FK
        if candidate.source == "coverage":
            item.coverage_result_id = candidate.decision_id
        elif candidate.source == "validation":
            item.validation_result_id = candidate.decision_id
        elif candidate.source == "teaching":
            item.teaching_analysis_id = candidate.decision_id
        elif candidate.source == "recommendation":
            item.recommendation_id = candidate.decision_id

        return item

    def _compute_importance(self, candidate: EvidenceCandidate) -> float:
        """Deterministic importance scoring based on source priority."""
        base_scores = {
            "validation": 1.0,
            "coverage": 0.9,
            "teaching": 0.8,
            "recommendation": 0.7,
        }
        return base_scores.get(candidate.source, 0.5)
