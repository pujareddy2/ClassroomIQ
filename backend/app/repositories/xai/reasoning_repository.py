"""
ReasoningRepository

Database operations for ReasoningStep.
Steps are always returned ordered by step_order ASC.
"""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.explanation_engine import ReasoningStep


class ReasoningRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_explanation(self, explanation_record_id: UUID) -> List[ReasoningStep]:
        """Return all reasoning steps for an explanation, ordered by step_order."""
        return (
            self.db.query(ReasoningStep)
            .filter(ReasoningStep.explanation_record_id == explanation_record_id)
            .order_by(ReasoningStep.step_order.asc())
            .all()
        )

    def save_step(self, step: ReasoningStep) -> ReasoningStep:
        self.db.add(step)
        self.db.flush()
        return step

    def batch_save_steps(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        """Batch insert all reasoning steps — single flush for performance."""
        for step in steps:
            self.db.add(step)
        self.db.flush()
        return steps

    def count_steps(self, explanation_record_id: UUID) -> int:
        return (
            self.db.query(ReasoningStep)
            .filter(ReasoningStep.explanation_record_id == explanation_record_id)
            .count()
        )

    def delete_by_explanation(self, explanation_record_id: UUID) -> int:
        rows = (
            self.db.query(ReasoningStep)
            .filter(ReasoningStep.explanation_record_id == explanation_record_id)
            .all()
        )
        for r in rows:
            self.db.delete(r)
        self.db.flush()
        return len(rows)
