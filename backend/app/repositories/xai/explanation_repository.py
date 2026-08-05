"""
ExplanationRepository

Database operations for ExplanationRecord.
Business logic belongs in services — this layer only touches the DB.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session, selectinload

from app.models.explanation_engine import (
    ConfidenceBreakdown,
    EvidenceItem,
    ExplanationRecord,
    ReasoningStep,
)


class ExplanationRepository:

    def __init__(self, db: Session):
        self.db = db

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_active(
        self,
        lecture_id: UUID,
        decision_source: str,
        decision_type: str,
        decision_id: Optional[UUID],
    ) -> Optional[ExplanationRecord]:
        """Return the single ACTIVE explanation for a specific decision, or None."""
        return (
            self.db.query(ExplanationRecord)
            .options(
                selectinload(ExplanationRecord.evidence_items),
                selectinload(ExplanationRecord.confidence_breakdown),
                selectinload(ExplanationRecord.reasoning_steps),
            )
            .filter(
                and_(
                    ExplanationRecord.lecture_id == lecture_id,
                    ExplanationRecord.decision_source == decision_source,
                    ExplanationRecord.decision_type == decision_type,
                    ExplanationRecord.decision_id == decision_id,
                    ExplanationRecord.status == "ACTIVE",
                )
            )
            .first()
        )

    def get_all_active_for_lecture(self, lecture_id: UUID) -> List[ExplanationRecord]:
        """Return all ACTIVE explanation records for a lecture, fully loaded."""
        return (
            self.db.query(ExplanationRecord)
            .options(
                selectinload(ExplanationRecord.evidence_items),
                selectinload(ExplanationRecord.confidence_breakdown),
                selectinload(ExplanationRecord.reasoning_steps),
            )
            .filter(
                ExplanationRecord.lecture_id == lecture_id,
                ExplanationRecord.status == "ACTIVE",
            )
            .all()
        )

    def get_by_id(self, record_id: UUID) -> Optional[ExplanationRecord]:
        return (
            self.db.query(ExplanationRecord)
            .options(
                selectinload(ExplanationRecord.evidence_items),
                selectinload(ExplanationRecord.confidence_breakdown),
                selectinload(ExplanationRecord.reasoning_steps),
            )
            .filter(ExplanationRecord.id == record_id)
            .first()
        )

    def get_by_source(
        self, lecture_id: UUID, decision_source: str
    ) -> List[ExplanationRecord]:
        """Return all ACTIVE records for a specific decision source."""
        return (
            self.db.query(ExplanationRecord)
            .filter(
                ExplanationRecord.lecture_id == lecture_id,
                ExplanationRecord.decision_source == decision_source,
                ExplanationRecord.status == "ACTIVE",
            )
            .all()
        )

    # ── Write ────────────────────────────────────────────────────────────────

    def supersede_existing(
        self,
        lecture_id: UUID,
        decision_source: str,
        decision_type: str,
        decision_id: Optional[UUID],
    ) -> int:
        """Mark all ACTIVE explanations for a decision as SUPERSEDED. Returns count updated."""
        rows = (
            self.db.query(ExplanationRecord)
            .filter(
                ExplanationRecord.lecture_id == lecture_id,
                ExplanationRecord.decision_source == decision_source,
                ExplanationRecord.decision_type == decision_type,
                ExplanationRecord.decision_id == decision_id,
                ExplanationRecord.status == "ACTIVE",
            )
            .all()
        )
        for r in rows:
            r.status = "SUPERSEDED"
        self.db.flush()
        return len(rows)

    def save(self, record: ExplanationRecord) -> ExplanationRecord:
        """Persist a new ExplanationRecord (flush, not commit — caller commits)."""
        self.db.add(record)
        self.db.flush()
        return record

    def count_active_for_lecture(self, lecture_id: UUID) -> int:
        return (
            self.db.query(ExplanationRecord)
            .filter(
                ExplanationRecord.lecture_id == lecture_id,
                ExplanationRecord.status == "ACTIVE",
            )
            .count()
        )
