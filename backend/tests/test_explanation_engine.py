"""
Unit tests for Explanation Quality Engine.
"""

from app.services.teaching.explanation_engine import ExplanationEngine


def test_explanation_engine_empty():
    engine = ExplanationEngine()
    res = engine.analyze([])
    assert res["score"] == 0.0
    assert "Empty transcript" in res["weaknesses"][0]


def test_explanation_engine_high_quality():
    engine = ExplanationEngine()
    chunks = [
        {
            "text": (
                "A compiler is defined as a computer program that translates computer code "
                "written in one programming language into another language. First, we start with lexical analysis. "
                "Second, we proceed to syntax analysis. Next, semantic analysis evaluates the parse tree. "
                "Finally, code generation produces machine code. Therefore, each step is logically structured."
            )
        }
    ]
    res = engine.analyze(chunks)
    assert res["score"] > 60.0
    assert res["definition_quality"] > 50.0
    assert res["step_by_step_clarity"] > 50.0
    assert len(res["strengths"]) >= 1
