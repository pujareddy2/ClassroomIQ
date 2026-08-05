"""
Unit tests for Module 4: Priority Ranking Engine.
"""

from app.services.recommendation.priority_engine import PriorityEngine
from app.services.recommendation.rule_engine import RawRecommendation


def test_priority_score_calculation():
    engine = PriorityEngine()
    # (90*0.35) + (80*0.30) + (50*0.20) + (90*0.15) = 31.5 + 24.0 + 10.0 + 13.5 = 79.0
    res = engine.calculate_priority(severity=90.0, impact=80.0, frequency=50.0, confidence=90.0)

    assert res.priority_score == 79.0
    assert res.priority_level == "HIGH"


def test_priority_levels():
    engine = PriorityEngine()

    critical = engine.calculate_priority(severity=95.0, impact=95.0, frequency=80.0, confidence=95.0)
    assert critical.priority_level == "CRITICAL"
    assert critical.priority_score >= 85.0

    low = engine.calculate_priority(severity=30.0, impact=30.0, frequency=30.0, confidence=50.0)
    assert low.priority_level in ("LOW", "INFORMATIONAL")


def test_priority_ranking_order():
    engine = PriorityEngine()
    r1 = RawRecommendation(
        recommendation_type="LOW_PRIO", category="Pedagogical", title="T1", reason="R1",
        recommended_action="A1", severity=30.0, impact=30.0
    )
    r2 = RawRecommendation(
        recommendation_type="HIGH_PRIO", category="Validation", title="T2", reason="R2",
        recommended_action="A2", severity=95.0, impact=90.0
    )

    ranked = engine.rank_recommendations([r1, r2])
    assert len(ranked) == 2
    assert ranked[0][0].recommendation_type == "HIGH_PRIO"
    assert ranked[0][1].priority_score > ranked[1][1].priority_score
