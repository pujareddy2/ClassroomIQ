"""
Unit tests for Classroom Interaction Engine.
"""

from app.services.teaching.interaction_engine import InteractionEngine


def test_interaction_engine_low_interaction():
    engine = InteractionEngine()
    chunks = [
        {"speaker": "Faculty", "text": "I will lecture continuously without asking anything."}
    ]
    res = engine.analyze(chunks)
    assert res["faculty_question_count"] == 0
    assert res["student_question_count"] == 0
    assert res["score"] == 0.0


def test_interaction_engine_high_interaction():
    engine = InteractionEngine()
    chunks = [
        {"speaker": "Faculty", "text": "Does anyone know what time complexity O(n log n) means?"},
        {"speaker": "Student", "text": "Is it log linear time complexity?"},
        {"speaker": "Faculty", "text": "Yes exactly! Is that clear for everyone?"},
    ]
    res = engine.analyze(chunks)
    assert res["faculty_question_count"] >= 1
    assert res["student_question_count"] >= 1
    assert res["clarification_requests"] >= 1
    assert res["score"] > 30.0
