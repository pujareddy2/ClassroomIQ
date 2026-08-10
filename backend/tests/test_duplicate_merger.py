"""
Unit tests for Module 5: Duplicate Recommendation Merger.
"""

from app.services.recommendation.duplicate_merger import DuplicateMerger
from app.services.recommendation.evidence_collector import EvidenceFact
from app.services.recommendation.rule_engine import RawRecommendation


def test_duplicate_merger_same_type():
    merger = DuplicateMerger()
    f1 = EvidenceFact(source="coverage", evidence_type="SKIPPED", description="Topic 1 skipped")
    f2 = EvidenceFact(source="coverage", evidence_type="SKIPPED", description="Topic 2 skipped")

    r1 = RawRecommendation(
        recommendation_type="TEACH_SKIPPED_TOPICS", category="Coverage", title="Title 1",
        reason="Reason 1", recommended_action="Action 1", severity=70.0, supporting_facts=[f1]
    )
    r2 = RawRecommendation(
        recommendation_type="TEACH_SKIPPED_TOPICS", category="Coverage", title="Title 2",
        reason="Reason 2", recommended_action="Action 2", severity=85.0, supporting_facts=[f2]
    )

    merged = merger.merge([r1, r2])
    assert len(merged) == 1
    assert merged[0].recommendation_type == "TEACH_SKIPPED_TOPICS"
    assert merged[0].severity == 85.0
    assert len(merged[0].supporting_facts) == 2


def test_duplicate_merger_distinct_types():
    merger = DuplicateMerger()
    r1 = RawRecommendation(
        recommendation_type="TEACH_SKIPPED_TOPICS", category="Coverage", title="Title 1",
        reason="Reason 1", recommended_action="Action 1"
    )
    r2 = RawRecommendation(
        recommendation_type="INCREASE_CLASSROOM_INTERACTION", category="Pedagogical", title="Title 2",
        reason="Reason 2", recommended_action="Action 2"
    )

    merged = merger.merge([r1, r2])
    assert len(merged) == 2
