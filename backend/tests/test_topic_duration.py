"""
Unit tests for DurationCalculator.
Tests: Rushed topic detection, over-explained topic detection, covered topic detection.
"""

from app.services.coverage.duration_calculator import DurationCalculator
from app.services.coverage.coverage_models import CoverageStatus


def test_duration_calculator_rushed():
    # Expected duration = 300s. Actual duration = 50s (< 40% threshold = 120s)
    chunks = [{"start_time": 0.0, "end_time": 50.0, "text": "Quick mention of compiler."}]
    exp, act, diff, over_pct, t1, t2, cnt, status = DurationCalculator.calculate_topic_durations(chunks, expected_hours=1)

    assert status == CoverageStatus.RUSHED
    assert act == 50.0
    assert diff < 0


def test_duration_calculator_over_explained():
    # Expected duration = 300s. Actual duration = 600s (> 160% threshold = 480s)
    chunks = [
        {"start_time": 0.0, "end_time": 300.0, "text": "Detailed explanation part 1."},
        {"start_time": 300.0, "end_time": 600.0, "text": "Detailed explanation part 2."},
    ]
    exp, act, diff, over_pct, t1, t2, cnt, status = DurationCalculator.calculate_topic_durations(chunks, expected_hours=1)

    assert status == CoverageStatus.OVER_EXPLAINED
    assert act == 600.0
    assert over_pct >= 50.0


def test_duration_calculator_covered():
    # Expected duration = 300s. Actual duration = 250s (Normal coverage)
    chunks = [
        {"start_time": 0.0, "end_time": 125.0, "text": "Part 1."},
        {"start_time": 125.0, "end_time": 250.0, "text": "Part 2."},
    ]
    exp, act, diff, over_pct, t1, t2, cnt, status = DurationCalculator.calculate_topic_durations(chunks, expected_hours=1)

    assert status == CoverageStatus.COVERED
    assert cnt == 2
