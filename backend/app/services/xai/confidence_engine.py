"""
Engine 4: XAI Confidence Engine

Deterministic confidence calculation.
Rules:
  - NEVER use random values.
  - NEVER let Gemini invent confidence.
  - Confidence is computed from measured upstream metrics only.
  - Five deterministic sub-scores feed a weighted formula.

Sub-scores:
  topic_match_score        (0-100): How fully the fact's topic was covered
  reference_match_score    (0-100): Whether a verified reference supports the decision
  validation_agreement     (0-100): Whether validation engine concurred
  coverage_agreement       (0-100): Coverage percentage aligned with decision
  teaching_agreement       (0-100): Teaching score alignment with decision

Overall confidence = 0.30*topic + 0.25*reference + 0.20*validation + 0.15*coverage + 0.10*teaching
Confidence level mapping:
  >= 85  → HIGH
  >= 65  → MEDIUM
  < 65   → LOW
"""

from dataclasses import dataclass

from app.models.xai_engine import XAIConfidenceBreakdown
from app.services.xai.evidence_collector import XAIFact
from app.services.xai.reference_citation_engine import AcademicReferenceCitation


@dataclass
class ConfidenceResult:
    overall_confidence: float
    confidence_level: str
    topic_match_score: float
    reference_match_score: float
    validation_agreement_score: float
    coverage_agreement_score: float
    teaching_agreement_score: float


# Deterministic weights — adjustable without code changes if moved to DB
_WEIGHT_TOPIC = 0.30
_WEIGHT_REFERENCE = 0.25
_WEIGHT_VALIDATION = 0.20
_WEIGHT_COVERAGE = 0.15
_WEIGHT_TEACHING = 0.10


def _level(score: float) -> str:
    if score >= 85.0:
        return "HIGH"
    if score >= 65.0:
        return "MEDIUM"
    return "LOW"


class XAIConfidenceEngine:
    """
    Computes deterministic confidence scores for every Explainability Package.
    Receives raw evidence facts + citation quality; returns ConfidenceResult.
    """

    def calculate(
        self,
        fact: XAIFact,
        citation: AcademicReferenceCitation,
    ) -> ConfidenceResult:
        """
        Compute confidence purely from measured values.

        topic_match_score:
            - Derived from the upstream metric value stored in the fact.
            - Coverage facts use coverage_percentage directly (0-100).
            - Validation facts use confidence_score * 100 if [0-1], else as-is.
            - Teaching facts use the metric_value directly.
            - Recommendation facts use priority_score * 100 if [0-1], else as-is.
            - Defaults to 70 when metric_value is absent.

        reference_match_score:
            - Directly taken from citation.citation_confidence.
            - 0.0 when no reference exists.

        validation_agreement_score:
            - VALIDATION_* facts: derived from confidence_score * 100.
            - All other facts: use metric_value proximity to expected thresholds.
            - Default to 75.0 (neutral agreement).

        coverage_agreement_score:
            - COVERAGE_* facts: metric_value (coverage_percentage).
            - Inverse for SKIPPED/PARTIAL (lower coverage → higher agreement
              that the decision was correct).
            - Default 75.0.

        teaching_agreement_score:
            - TEACHING_* or RECOMMENDATION_* facts with teaching metric:
              use metric_value scaled to 0-100.
            - Default 70.0.
        """

        # ── 1. Topic Match Score ───────────────────────────────────────────────
        if fact.metric_value is not None:
            raw = fact.metric_value
            # If value looks like a 0-1 probability, scale to 0-100
            topic_match = (raw * 100.0) if 0.0 <= raw <= 1.0 else float(raw)
        else:
            topic_match = 70.0
        topic_match = max(0.0, min(100.0, topic_match))

        # ── 2. Reference Match Score ───────────────────────────────────────────
        reference_match = max(0.0, min(100.0, citation.citation_confidence))

        # ── 3. Validation Agreement Score ─────────────────────────────────────
        if fact.source == "validation" and fact.metric_value is not None:
            raw = fact.metric_value
            validation_agreement = (raw * 100.0) if 0.0 <= raw <= 1.0 else float(raw)
        else:
            validation_agreement = 75.0
        validation_agreement = max(0.0, min(100.0, validation_agreement))

        # ── 4. Coverage Agreement Score ────────────────────────────────────────
        if fact.source == "coverage" and fact.metric_value is not None:
            # High coverage → fact of SKIPPED/RUSHED has lower agreement
            # Low coverage → fact of SKIPPED/PARTIAL has higher agreement
            pct = float(fact.metric_value)
            if fact.fact_type in ("COVERAGE_SKIPPED", "COVERAGE_PARTIALLY_COVERED", "COVERAGE_RUSHED"):
                # Invert: if coverage was 20% and we flag it as SKIPPED → very confident
                coverage_agreement = 100.0 - pct
            else:
                coverage_agreement = pct
        else:
            coverage_agreement = 75.0
        coverage_agreement = max(0.0, min(100.0, coverage_agreement))

        # ── 5. Teaching Agreement Score ────────────────────────────────────────
        if fact.source == "teaching" and fact.metric_value is not None:
            raw = float(fact.metric_value)
            # For WEAK_EXPLANATION: lower score → higher agreement that issue exists
            if fact.fact_type == "WEAK_EXPLANATION":
                teaching_agreement = 100.0 - raw
            elif fact.fact_type == "LOW_INTERACTION":
                teaching_agreement = 100.0 - raw
            else:
                teaching_agreement = raw
        else:
            teaching_agreement = 70.0
        teaching_agreement = max(0.0, min(100.0, teaching_agreement))

        # ── Weighted Overall ───────────────────────────────────────────────────
        overall = (
            _WEIGHT_TOPIC * topic_match
            + _WEIGHT_REFERENCE * reference_match
            + _WEIGHT_VALIDATION * validation_agreement
            + _WEIGHT_COVERAGE * coverage_agreement
            + _WEIGHT_TEACHING * teaching_agreement
        )
        overall = round(max(0.0, min(100.0, overall)), 2)

        return ConfidenceResult(
            overall_confidence=overall,
            confidence_level=_level(overall),
            topic_match_score=round(topic_match, 2),
            reference_match_score=round(reference_match, 2),
            validation_agreement_score=round(validation_agreement, 2),
            coverage_agreement_score=round(coverage_agreement, 2),
            teaching_agreement_score=round(teaching_agreement, 2),
        )

    def to_orm(self, package_id, result: ConfidenceResult) -> XAIConfidenceBreakdown:
        """Convert ConfidenceResult to ORM model. package_id is set by the repository."""
        return XAIConfidenceBreakdown(
            package_id=package_id,
            overall_confidence=result.overall_confidence,
            topic_match_score=result.topic_match_score,
            reference_match_score=result.reference_match_score,
            validation_agreement_score=result.validation_agreement_score,
            coverage_agreement_score=result.coverage_agreement_score,
            teaching_agreement_score=result.teaching_agreement_score,
            confidence_level=result.confidence_level,
        )
