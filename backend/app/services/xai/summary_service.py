"""
SummaryService

Computes lecture-level Explainability summary statistics.

After all ExplanationRecords are built for a lecture, this service
calculates aggregate metrics and persists them via SummaryRepository.
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.explanation_engine import ExplanationRecord
from app.repositories.xai.summary_repository import SummaryRepository

logger = logging.getLogger(__name__)


class SummaryService:

    def __init__(self, db: Session):
        self.db = db
        self._repo = SummaryRepository(db)

    def compute_and_save(
        self,
        lecture_id: UUID,
        records: List[ExplanationRecord],
        processing_time: float,
    ) -> dict:
        """
        Compute aggregate summary from built records and upsert into DB.

        Returns a dict with summary statistics.
        """
        total = len(records)
        if total == 0:
            summary = self._repo.upsert(
                lecture_id=lecture_id,
                total_explanations=0,
                average_confidence=0.0,
                highest_confidence=0.0,
                lowest_confidence=0.0,
                processing_time=processing_time,
            )
            self.db.flush()
            return self._to_dict(summary)

        confidences = [r.overall_confidence for r in records]
        avg = round(sum(confidences) / total, 2)
        highest = round(max(confidences), 2)
        lowest = round(min(confidences), 2)

        summary = self._repo.upsert(
            lecture_id=lecture_id,
            total_explanations=total,
            average_confidence=avg,
            highest_confidence=highest,
            lowest_confidence=lowest,
            processing_time=round(processing_time, 3),
        )
        self.db.flush()

        logger.info(
            "Summary computed — lecture_id=%s, total=%d, avg_conf=%.2f",
            lecture_id, total, avg,
        )

        return self._to_dict(summary)

    def get_summary(self, lecture_id: UUID) -> dict:
        """Retrieve existing summary for a lecture."""
        summary = self._repo.get_by_lecture(lecture_id)
        if summary is None:
            return {
                "lecture_id": str(lecture_id),
                "total_explanations": 0,
                "average_confidence": 0.0,
                "highest_confidence": 0.0,
                "lowest_confidence": 0.0,
                "processing_time": 0.0,
            }
        return self._to_dict(summary)

    @staticmethod
    def _to_dict(summary) -> dict:
        return {
            "lecture_id": str(summary.lecture_id),
            "total_explanations": summary.total_explanations,
            "average_confidence": summary.average_confidence,
            "highest_confidence": summary.highest_confidence,
            "lowest_confidence": summary.lowest_confidence,
            "processing_time": summary.processing_time,
        }
