"""
ConfidenceRepository

Database operations for ConfidenceBreakdown.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.explanation_engine import ConfidenceBreakdown


class ConfidenceRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_explanation(self, explanation_record_id: UUID) -> Optional[ConfidenceBreakdown]:
        return (
            self.db.query(ConfidenceBreakdown)
            .filter(ConfidenceBreakdown.explanation_record_id == explanation_record_id)
            .first()
        )

    def save(self, breakdown: ConfidenceBreakdown) -> ConfidenceBreakdown:
        self.db.add(breakdown)
        self.db.flush()
        return breakdown

    def update_overall(self, explanation_record_id: UUID, overall: float) -> bool:
        """Update the overall_confidence of an existing breakdown. Returns True if found."""
        bd = self.get_by_explanation(explanation_record_id)
        if bd:
            bd.overall_confidence = overall
            self.db.flush()
            return True
        return False
