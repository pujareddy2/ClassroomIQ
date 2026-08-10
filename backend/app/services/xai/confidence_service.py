"""
ConfidenceService

Computes deterministic confidence scores for each Explainability Package.

Formula:
  overall = 0.25 * topic_match_score
          + 0.20 * coverage_score
          + 0.20 * validation_score
          + 0.15 * reference_score
          + 0.10 * teaching_score
          + 0.10 * recommendation_score

Rules:
  - NEVER use random values.
  - NEVER let Gemini invent confidence.
  - Confidence is computed exclusively from measured upstream metrics.
  - All sub-scores are clamped to [0.0, 100.0].
"""

import logging
from dataclasses import dataclass
from typing import Optional

from app.models.explanation_engine import ConfidenceBreakdown
from app.services.xai.evidence_collector import EvidenceCandidate

logger = logging.getLogger(__name__)

# Deterministic weights
_W_TOPIC = 0.25
_W_COVERAGE = 0.20
_W_VALIDATION = 0.20
_W_REFERENCE = 0.15
_W_TEACHING = 0.10
_W_RECOMMENDATION = 0.10


@dataclass
class ConfidenceResult:
    topic_match_score: float
    coverage_score: float
    validation_score: float
    reference_score: float
    teaching_score: float
    recommendation_score: float
    overall_confidence: float


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _scale(value: Optional[float]) -> float:
    """Scale a raw metric value to 0-100. Values in [0,1] are treated as fractions."""
    if value is None:
        return 70.0  # neutral default
    if 0.0 <= value <= 1.0:
        return value * 100.0
    return float(value)


class ConfidenceService:
    """
    Computes deterministic confidence scores per explanation.
    No DB access — pure computation on the EvidenceCandidate + citation confidence.
    """

    def calculate(
        self,
        candidate: EvidenceCandidate,
        citation_confidence: float,
    ) -> ConfidenceResult:
        """Compute confidence purely from measured values."""
        logger.info("Confidence Calculated — source=%s, type=%s", candidate.source, candidate.decision_type)

        # ── topic_match_score: derived from the upstream metric ───────────────
        topic_match = _clamp(_scale(candidate.metric_value))

        # ── reference_score: citation confidence directly ─────────────────────
        reference = _clamp(citation_confidence)

        # ── coverage_score ────────────────────────────────────────────────────
        if candidate.source == "coverage" and candidate.metric_value is not None:
            pct = float(candidate.metric_value)
            # For flagged topics: low coverage → high confidence that the flag is correct
            if "SKIPPED" in candidate.decision_type or "PARTIALLY" in candidate.decision_type or "RUSHED" in candidate.decision_type:
                coverage = _clamp(100.0 - pct)
            else:
                coverage = _clamp(pct)
        else:
            coverage = 75.0

        # ── validation_score ──────────────────────────────────────────────────
        if candidate.source == "validation" and candidate.metric_value is not None:
            validation = _clamp(_scale(candidate.metric_value))
        else:
            validation = 75.0

        # ── teaching_score ────────────────────────────────────────────────────
        if candidate.source == "teaching" and candidate.metric_value is not None:
            raw = float(candidate.metric_value)
            # Low teaching score → high confidence that the weakness is real
            if "WEAK" in candidate.decision_type or "LOW" in candidate.decision_type or "POOR" in candidate.decision_type:
                teaching = _clamp(100.0 - raw)
            else:
                teaching = _clamp(raw)
        else:
            teaching = 70.0

        # ── recommendation_score ──────────────────────────────────────────────
        if candidate.source == "recommendation" and candidate.metric_value is not None:
            recommendation = _clamp(_scale(candidate.metric_value))
        else:
            recommendation = 70.0

        # ── Weighted overall ──────────────────────────────────────────────────
        overall = round(
            _W_TOPIC * topic_match
            + _W_COVERAGE * coverage
            + _W_VALIDATION * validation
            + _W_REFERENCE * reference
            + _W_TEACHING * teaching
            + _W_RECOMMENDATION * recommendation,
            2,
        )
        overall = _clamp(overall)

        return ConfidenceResult(
            topic_match_score=round(topic_match, 2),
            coverage_score=round(coverage, 2),
            validation_score=round(validation, 2),
            reference_score=round(reference, 2),
            teaching_score=round(teaching, 2),
            recommendation_score=round(recommendation, 2),
            overall_confidence=overall,
        )

    def to_orm(
        self, explanation_record_id, result: ConfidenceResult
    ) -> ConfidenceBreakdown:
        """Convert ConfidenceResult to ORM model for persistence."""
        return ConfidenceBreakdown(
            explanation_record_id=explanation_record_id,
            topic_match_score=result.topic_match_score,
            coverage_score=result.coverage_score,
            validation_score=result.validation_score,
            reference_score=result.reference_score,
            teaching_score=result.teaching_score,
            recommendation_score=result.recommendation_score,
            overall_confidence=result.overall_confidence,
        )
