"""
Unit tests for Module 1: Evidence Collector.
"""

import uuid
from app.services.recommendation.evidence_collector import EvidenceBundle, EvidenceFact


def test_evidence_bundle_creation():
    lec_id = uuid.uuid4()
    bundle = EvidenceBundle(
        lecture_id=lec_id,
        weighted_coverage_pct=62.5,
        skipped_topics_count=2,
        formula_errors_count=3,
        incorrect_concepts_count=1,
        explanation_score=45.0,
        example_score=50.0,
        structure_score=55.0,
        interaction_score=35.0,
    )

    assert bundle.lecture_id == lec_id
    assert bundle.weighted_coverage_pct == 62.5
    assert bundle.skipped_topics_count == 2
    assert bundle.formula_errors_count == 3
    assert bundle.incorrect_concepts_count == 1
    assert bundle.explanation_score == 45.0


def test_evidence_fact_attributes():
    fact = EvidenceFact(
        source="coverage",
        evidence_type="SKIPPED_TOPICS",
        description="2 topics skipped",
        metric_name="skipped_topics",
        metric_value=2.0,
        threshold=0.0,
        severity_level="HIGH",
    )
    assert fact.source == "coverage"
    assert fact.evidence_type == "SKIPPED_TOPICS"
    assert fact.metric_value == 2.0
    assert fact.severity_level == "HIGH"
