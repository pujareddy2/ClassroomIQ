"""
Confidence Calculator component for Technical Validation Engine.
Calculates 0-100 score and assigns HIGH, MEDIUM, LOW confidence levels.
"""

from __future__ import annotations

from app.services.validation.validation_models import SeverityLevel


class ConfidenceCalculator:
    """Calculates weighted confidence score (0-100) and maps to SeverityLevel (HIGH, MEDIUM, LOW)."""

    @staticmethod
    def calculate(
        match_confidence: float,
        evidence_count: int,
        raw_score: float = 85.0,
    ) -> tuple[float, SeverityLevel]:
        """
        Factors:
          - match_confidence (0.0 to 1.0)
          - evidence_count (number of supporting reference sources)
          - raw_score (base engine/LLM score)
        """
        # Weightings
        weight_match = min(1.0, match_confidence) * 20.0
        weight_evidence = min(3, evidence_count) * 10.0
        weight_base = (raw_score / 100.0) * 50.0

        final_score = round(weight_match + weight_evidence + weight_base, 1)
        final_score = max(0.0, min(100.0, final_score))

        if final_score >= 80.0:
            level = SeverityLevel.HIGH
        elif final_score >= 50.0:
            level = SeverityLevel.MEDIUM
        else:
            level = SeverityLevel.LOW

        return final_score, level
