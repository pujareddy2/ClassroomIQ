"""
Unit tests for SequenceVerifier.
Tests: Correct teaching sequence, out of order teaching, skipped prerequisites.
"""

from app.services.coverage.sequence_verifier import SequenceVerifier
from app.services.coverage.coverage_models import SequenceStatus


def test_sequence_verifier_correct_order():
    # Topics 1, 2, 3 taught in order at t=0s, 100s, 200s
    covered = [(1, 0.0), (2, 100.0), (3, 200.0)]
    mapping, score = SequenceVerifier.verify_sequence(covered, 3)

    assert score == 100.0
    assert mapping[1][1] == SequenceStatus.CORRECT_SEQUENCE
    assert mapping[2][1] == SequenceStatus.CORRECT_SEQUENCE
    assert mapping[3][1] == SequenceStatus.CORRECT_SEQUENCE


def test_sequence_verifier_out_of_order():
    # Topic 3 taught BEFORE Topic 1
    covered = [(3, 10.0), (1, 100.0)]
    mapping, score = SequenceVerifier.verify_sequence(covered, 3)

    assert score < 100.0
    assert mapping[3][1] == SequenceStatus.SKIPPED_PREREQUISITE
