"""
SummaryRepository

Database operations for ExplanationSummary (lecture-level aggregates).
Supports upsert: if a summary already exists for a lecture, it is updated.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.explanation_engine import ExplanationSummary


class SummaryRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_lecture(self, lecture_id: UUID) -> Optional[ExplanationSummary]:
        return (
            self.db.query(ExplanationSummary)
            .filter(ExplanationSummary.lecture_id == lecture_id)
            .first()
        )

    def upsert(
        self,
        lecture_id: UUID,
        total_explanations: int,
        average_confidence: float,
        highest_confidence: float,
        lowest_confidence: float,
        processing_time: float,
    ) -> ExplanationSummary:
        """Insert or update the lecture-level summary. Returns the saved record."""
        existing = self.get_by_lecture(lecture_id)
        if existing:
            existing.total_explanations = total_explanations
            existing.average_confidence = average_confidence
            existing.highest_confidence = highest_confidence
            existing.lowest_confidence = lowest_confidence
            existing.processing_time = processing_time
            self.db.flush()
            return existing

        summary = ExplanationSummary(
            lecture_id=lecture_id,
            total_explanations=total_explanations,
            average_confidence=average_confidence,
            highest_confidence=highest_confidence,
            lowest_confidence=lowest_confidence,
            processing_time=processing_time,
        )
        self.db.add(summary)
        self.db.flush()
        return summary

    def delete_by_lecture(self, lecture_id: UUID) -> bool:
        existing = self.get_by_lecture(lecture_id)
        if existing:
            self.db.delete(existing)
            self.db.flush()
            return True
        return False
