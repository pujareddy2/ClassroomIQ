"""
Unit tests for Example Detection Engine.
"""

from app.services.teaching.example_engine import ExampleEngine


def test_example_engine_no_examples():
    engine = ExampleEngine()
    chunks = [{"text": "Today we discuss simple concepts without any specific instances."}]
    res = engine.analyze(chunks)
    assert res["score"] == 0.0
    assert res["example_count"] == 0


def test_example_engine_multiple_types():
    engine = ExampleEngine()
    chunks = [
        {
            "text": "For example, in real life a bank transaction requires atomic updates.",
            "start_time": 0.0,
            "end_time": 10.0,
        },
        {
            "text": "Let's look at python code function def calculate_tax(amount): return amount * 0.2",
            "start_time": 10.0,
            "end_time": 20.0,
        },
        {
            "text": "Let's compute the value of 5 + 10 equals 15.",
            "start_time": 20.0,
            "end_time": 30.0,
        },
    ]
    res = engine.analyze(chunks)
    assert res["example_count"] >= 3
    assert res["example_diversity"] >= 3
    assert res["score"] > 50.0
