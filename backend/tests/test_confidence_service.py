"""
Unit tests for ConfidenceService.
"""

from uuid import uuid4
import pytest
from app.services.xai.confidence_service import ConfidenceService
from app.services.xai.evidence_collector import EvidenceCandidate


def test_confidence_calculation():
    service = ConfidenceService()

    candidate = EvidenceCandidate(
        source="coverage",
        decision_type="COVERAGE_SKIPPED",
        decision_id=uuid4(),
        subject="Recursion",
        description="Recursion was skipped",
        metric_name="coverage_percentage",
        metric_value=20.0,
    )

    res = service.calculate(candidate, citation_confidence=90.0)

    assert res.topic_match_score == 20.0
    assert res.reference_score == 90.0
    assert res.coverage_score == 80.0  # 100 - 20 for SKIPPED
    assert 0.0 <= res.overall_confidence <= 100.0


def test_confidence_clamping_and_scaling():
    service = ConfidenceService()

    # Probability 0-1 metric
    candidate = EvidenceCandidate(
        source="validation",
        decision_type="VALIDATION_INCORRECT",
        decision_id=uuid4(),
        subject="Syntax",
        description="Syntax error",
        metric_name="confidence_score",
        metric_value=0.95,
    )

    res = service.calculate(candidate, citation_confidence=95.0)

    assert res.topic_match_score == 95.0
    assert res.validation_score == 95.0
    assert res.overall_confidence > 70.0
