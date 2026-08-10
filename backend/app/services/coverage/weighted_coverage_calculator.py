"""
Weighted Coverage Calculator component for Curriculum Coverage Intelligence Engine.
Computes weighted coverage percentage using topic importance weights.
"""

from __future__ import annotations

from typing import List, Tuple
from app.services.coverage.coverage_models import CoverageStatus


class WeightedCoverageCalculator:
    """Calculates weighted coverage percentage: (sum of covered weights / sum of total weights) * 100."""

    @staticmethod
    def calculate_weighted_coverage(
        topic_weight_status_list: List[Tuple[float, CoverageStatus, float]],
        # [(importance_weight, status, coverage_percentage), ...]
    ) -> Tuple[float, float]:
        """
        Returns:
            (raw_coverage_percentage, weighted_coverage_percentage)
        """
        if not topic_weight_status_list:
            return 0.0, 0.0

        total_topics = len(topic_weight_status_list)
        total_weight = 0.0
        weighted_covered_sum = 0.0
        covered_count = 0

        for weight, status, pct in topic_weight_status_list:
            w = max(0.1, weight if weight > 0 else 1.0)
            total_weight += w

            if status in (CoverageStatus.COVERED, CoverageStatus.OVER_EXPLAINED, CoverageStatus.REPEATED):
                covered_count += 1
                weighted_covered_sum += w
            elif status in (CoverageStatus.PARTIALLY_COVERED, CoverageStatus.RUSHED):
                coverage_factor = (pct / 100.0) if pct > 0 else 0.5
                weighted_covered_sum += w * coverage_factor
                covered_count += 0.5

        raw_pct = round((covered_count / float(total_topics)) * 100.0, 1)
        weighted_pct = round((weighted_covered_sum / float(total_weight)) * 100.0, 1) if total_weight > 0 else 0.0

        return raw_pct, weighted_pct
