"""
Duration Calculator component for Curriculum Coverage Intelligence Engine.
Computes expected vs actual duration and detects rushed vs over-explained topics based on configurable threshold ratios.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple
from app.services.coverage.coverage_models import CoverageStatus

logger = logging.getLogger(__name__)

# Configurable Threshold Ratios
RUSHED_THRESHOLD_RATIO = 0.40       # If actual < 40% of expected duration => RUSHED
OVER_EXPLAINED_THRESHOLD_RATIO = 1.60  # If actual > 160% of expected duration => OVER_EXPLAINED


class DurationCalculator:
    """Calculates teaching durations and classifies rushed/over-explained topics."""

    @staticmethod
    def calculate_topic_durations(
        topic_chunks: List[dict],
        expected_hours: int = 1,
        default_expected_seconds: float = 300.0,
    ) -> Tuple[float, float, float, float, float, float, int, CoverageStatus]:
        """
        Returns:
            (expected_sec, actual_sec, diff_sec, over_explained_pct, first_time, last_time, occurrence_count, status_override)
        """
        if not topic_chunks:
            expected_sec = expected_hours * 60.0 * 5.0  # Normalized for 1 hour topic = 300s in 50m lecture
            return expected_sec, 0.0, -expected_sec, 0.0, None, None, 0, CoverageStatus.SKIPPED

        first_time = min(c["start_time"] for c in topic_chunks)
        last_time = max(c["end_time"] for c in topic_chunks)
        occurrence_count = len(topic_chunks)

        # Actual duration = sum of non-overlapping chunk intervals
        actual_sec = sum(max(0.0, c["end_time"] - c["start_time"]) for c in topic_chunks)

        # Expected duration: default 300s (5 mins) per topic unit unless specified
        expected_sec = expected_hours * default_expected_seconds

        diff_sec = round(actual_sec - expected_sec, 1)

        over_explained_pct = 0.0
        if expected_sec > 0:
            over_explained_pct = round(max(0.0, ((actual_sec - expected_sec) / expected_sec) * 100.0), 1)

        # Classification
        if actual_sec < (expected_sec * RUSHED_THRESHOLD_RATIO):
            status = CoverageStatus.RUSHED
        elif actual_sec > (expected_sec * OVER_EXPLAINED_THRESHOLD_RATIO):
            status = CoverageStatus.OVER_EXPLAINED
        elif occurrence_count > 1 and actual_sec >= (expected_sec * 0.7):
            status = CoverageStatus.COVERED
        else:
            status = CoverageStatus.PARTIALLY_COVERED

        return (
            round(expected_sec, 1),
            round(actual_sec, 1),
            diff_sec,
            over_explained_pct,
            first_time,
            last_time,
            occurrence_count,
            status,
        )
