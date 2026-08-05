"""
Unit tests for Module 2: Recommendation Rule Engine.
"""

import uuid
from app.services.recommendation.evidence_collector import EvidenceBundle, EvidenceFact
from app.services.recommendation.rule_engine import RecommendationRuleEngine


def test_rule_engine_low_coverage_and_skipped():
    engine = RecommendationRuleEngine()
    bundle = EvidenceBundle(
        lecture_id=uuid.uuid4(),
        weighted_coverage_pct=55.0,
        skipped_topics_count=2,
    )
    bundle.coverage_facts.append(
        EvidenceFact(source="coverage", evidence_type="LOW_COVERAGE", description="Low coverage")
    )
    bundle.coverage_facts.append(
        EvidenceFact(source="coverage", evidence_type="SKIPPED_TOPICS", description="Skipped 2 topics")
    )

    recs = engine.evaluate(bundle)
    types = [r.recommendation_type for r in recs]

    assert "IMPROVE_CURRICULUM_COVERAGE" in types
    assert "TEACH_SKIPPED_TOPICS" in types


def test_rule_engine_validation_issues():
    engine = RecommendationRuleEngine()
    bundle = EvidenceBundle(
        lecture_id=uuid.uuid4(),
        formula_errors_count=3,
        incorrect_concepts_count=1,
    )

    recs = engine.evaluate(bundle)
    types = [r.recommendation_type for r in recs]

    assert "REVIEW_MATHEMATICAL_DERIVATIONS" in types
    assert "CORRECT_CONCEPTUAL_ACCURACY" in types


def test_rule_engine_pedagogical_weaknesses():
    engine = RecommendationRuleEngine()
    bundle = EvidenceBundle(
        lecture_id=uuid.uuid4(),
        explanation_score=40.0,
        example_score=45.0,
        interaction_score=30.0,
        structure_score=50.0,
    )

    recs = engine.evaluate(bundle)
    types = [r.recommendation_type for r in recs]

    assert "IMPROVE_EXPLANATION_QUALITY" in types
    assert "ADD_REAL_WORLD_EXAMPLES" in types
    assert "INCREASE_CLASSROOM_INTERACTION" in types
    assert "IMPROVE_LECTURE_ORGANIZATION" in types


def test_rule_engine_excellent_lecture():
    engine = RecommendationRuleEngine()
    bundle = EvidenceBundle(
        lecture_id=uuid.uuid4(),
        weighted_coverage_pct=95.0,
        skipped_topics_count=0,
        formula_errors_count=0,
        incorrect_concepts_count=0,
        explanation_score=90.0,
        example_score=85.0,
        structure_score=90.0,
        interaction_score=80.0,
    )

    recs = engine.evaluate(bundle)
    assert len(recs) == 0
