"""
EvidenceRepository

Database operations for EvidenceItem and its children
(TranscriptEvidence, ReferenceCitation).
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.explanation_engine import (
    EvidenceItem,
    ReferenceCitation,
    TranscriptEvidence,
)


class EvidenceRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_by_explanation(self, explanation_record_id: UUID) -> List[EvidenceItem]:
        """Return all evidence items for an explanation, with transcript + citation loaded."""
        return (
            self.db.query(EvidenceItem)
            .options(
                selectinload(EvidenceItem.transcript_evidence),
                selectinload(EvidenceItem.reference_citation),
            )
            .filter(EvidenceItem.explanation_record_id == explanation_record_id)
            .all()
        )

    def get_by_id(self, evidence_id: UUID) -> Optional[EvidenceItem]:
        return (
            self.db.query(EvidenceItem)
            .options(
                selectinload(EvidenceItem.transcript_evidence),
                selectinload(EvidenceItem.reference_citation),
            )
            .filter(EvidenceItem.id == evidence_id)
            .first()
        )

    def get_by_coverage_result(self, coverage_result_id: UUID) -> List[EvidenceItem]:
        return (
            self.db.query(EvidenceItem)
            .filter(EvidenceItem.coverage_result_id == coverage_result_id)
            .all()
        )

    def get_by_validation_result(self, validation_result_id: UUID) -> List[EvidenceItem]:
        return (
            self.db.query(EvidenceItem)
            .filter(EvidenceItem.validation_result_id == validation_result_id)
            .all()
        )

    # ── Write ────────────────────────────────────────────────────────────────

    def save_evidence_item(self, item: EvidenceItem) -> EvidenceItem:
        self.db.add(item)
        self.db.flush()
        return item

    def save_transcript_evidence(self, te: TranscriptEvidence) -> TranscriptEvidence:
        self.db.add(te)
        self.db.flush()
        return te

    def save_reference_citation(self, rc: ReferenceCitation) -> ReferenceCitation:
        self.db.add(rc)
        self.db.flush()
        return rc

    def batch_save_evidence_items(self, items: List[EvidenceItem]) -> List[EvidenceItem]:
        """Batch insert evidence items — all flushed together for performance."""
        for item in items:
            self.db.add(item)
        self.db.flush()
        return items

    def delete_by_explanation(self, explanation_record_id: UUID) -> int:
        """Cascade delete is handled by DB, but this allows explicit batch delete."""
        rows = (
            self.db.query(EvidenceItem)
            .filter(EvidenceItem.explanation_record_id == explanation_record_id)
            .all()
        )
        for r in rows:
            self.db.delete(r)
        self.db.flush()
        return len(rows)
