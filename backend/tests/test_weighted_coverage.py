"""
Unit tests for WeightedCoverageCalculator.
Tests: Weighted coverage percentage formula calculations.
"""

from app.services.coverage.weighted_coverage_calculator import WeightedCoverageCalculator
from app.services.coverage.coverage_models import CoverageStatus


def test_weighted_coverage_all_covered():
    items = [
        (2.0, CoverageStatus.COVERED, 100.0),
        (1.0, CoverageStatus.COVERED, 100.0),
    ]
    raw, weighted = WeightedCoverageCalculator.calculate_weighted_coverage(items)
    assert raw == 100.0
    assert weighted == 100.0


def test_weighted_coverage_mixed_importance():
    # Topic 1 (high importance weight = 3.0) covered 100%
    # Topic 2 (low importance weight = 1.0) skipped 0%
    items = [
        (3.0, CoverageStatus.COVERED, 100.0),
        (1.0, CoverageStatus.SKIPPED, 0.0),
    ]
    raw, weighted = WeightedCoverageCalculator.calculate_weighted_coverage(items)
    assert raw == 50.0  # 1 of 2 topics covered
    assert weighted == 75.0  # (3.0 / 4.0) * 100 = 75.0%
