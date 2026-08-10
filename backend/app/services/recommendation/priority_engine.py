"""
Module 4: Priority Ranking Engine

Calculates deterministic priority scores and assigns priority levels using the formula:
Priority Score = (Severity × 35%) + (Impact × 30%) + (Frequency × 20%) + (Confidence × 15%)

Priority Levels:
  CRITICAL      ≥ 85.0
  HIGH          ≥ 70.0
  MEDIUM        ≥ 50.0
  LOW           ≥ 30.0
  INFORMATIONAL < 30.0

Never allows LLM to assign priority.
"""

from dataclasses import dataclass
from typing import List, Tuple

from app.services.recommendation.rule_engine import RawRecommendation


@dataclass
class PriorityResult:
    priority_score: float
    priority_level: str
    severity: float
    impact: float
    urgency: float
    frequency: float
    confidence: float


class PriorityEngine:

    # Formula weights
    SEVERITY_WEIGHT = 0.35
    IMPACT_WEIGHT = 0.30
    FREQUENCY_WEIGHT = 0.20
    CONFIDENCE_WEIGHT = 0.15

    def calculate_priority(
        self,
        severity: float,
        impact: float,
        frequency: float = 50.0,
        confidence: float = 85.0,
        urgency: float = 50.0,
    ) -> PriorityResult:
        """Calculate weighted priority score and level."""
        score = (
            (severity * self.SEVERITY_WEIGHT)
            + (impact * self.IMPACT_WEIGHT)
            + (frequency * self.FREQUENCY_WEIGHT)
            + (confidence * self.CONFIDENCE_WEIGHT)
        )
        score = round(min(100.0, max(0.0, score)), 2)
        level = self._assign_level(score)

        return PriorityResult(
            priority_score=score,
            priority_level=level,
            severity=severity,
            impact=impact,
            urgency=urgency,
            frequency=frequency,
            confidence=confidence,
        )

    def rank_recommendations(
        self, raw_recs: List[RawRecommendation]
    ) -> List[Tuple[RawRecommendation, PriorityResult]]:
        """Rank raw recommendations by calculated priority score in descending order."""
        ranked = []
        for rec in raw_recs:
            # Determine frequency from supporting facts count
            fact_count = len(rec.supporting_facts)
            freq = min(100.0, 40.0 + (fact_count * 15.0))

            p_res = self.calculate_priority(
                severity=rec.severity,
                impact=rec.impact,
                frequency=freq,
                confidence=rec.confidence,
                urgency=rec.urgency,
            )
            ranked.append((rec, p_res))

        # Sort descending by priority score
        return sorted(ranked, key=lambda x: x[1].priority_score, reverse=True)

    @staticmethod
    def _assign_level(score: float) -> str:
        if score >= 85.0:
            return "CRITICAL"
        if score >= 70.0:
            return "HIGH"
        if score >= 50.0:
            return "MEDIUM"
        if score >= 30.0:
            return "LOW"
        return "INFORMATIONAL"
