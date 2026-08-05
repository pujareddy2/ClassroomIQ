"""
Unit tests for Teaching Structure Engine.
"""

from app.services.teaching.structure_engine import StructureEngine


def test_structure_engine_complete_flow():
    engine = StructureEngine()
    chunks = [
        {"text": "Welcome everyone. In this lecture, today we will discuss sorting algorithms."},
        {"text": "Quick sort is a divide and conquer algorithm."},
        {"text": "For example, partitioning around a pivot element."},
        {"text": "To summarize, today we covered quicksort efficiency and pivot selection."},
    ]
    res = engine.analyze(chunks)
    assert res["has_introduction"] is True
    assert res["has_conclusion"] is True
    assert res["score"] >= 50.0
    assert "Introduction" in res["detected_flow"]
    assert "Summary & Conclusion" in res["detected_flow"]


def test_structure_engine_missing_intro_conclusion():
    engine = StructureEngine()
    chunks = [
        {"text": "Just jumping straight into quicksort partitioning logic without saying hello."},
    ]
    res = engine.analyze(chunks)
    assert res["has_introduction"] is False
    assert res["has_conclusion"] is False
