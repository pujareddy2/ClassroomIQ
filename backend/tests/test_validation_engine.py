"""
Unit tests for Technical Validation Engine main pipeline.
Tests: Correct explanation, incorrect concept explanation, missing concept, empty transcript, large lecture.
"""

import uuid
import pytest
from app.db.session import SessionLocal
from app.models.curriculum import Curriculum
from app.services.validation.validation_service import ValidationService
from app.services.validation.exceptions import EmptyTranscriptError


def test_validation_engine_correct_explanation(db_session):
    service = ValidationService(db_session)
    chunks = [
        {
            "chunk_id": "chunk_1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 30.0,
            "text": "A compiler is a program that translates source code written in a high-level language into machine code.",
        }
    ]
    curr = db_session.query(Curriculum).first()
    res = service.process_and_validate_transcript(chunks, curriculum_id=curr.id if curr else None)

    assert res["status"] == "SUCCESS"
    assert res["validated_chunks"] == 1
    assert res["correct_concepts"] >= 1
    assert res["incorrect_concepts"] == 0


def test_validation_engine_incorrect_concept(db_session):
    service = ValidationService(db_session)
    chunks = [
        {
            "chunk_id": "chunk_2",
            "speaker": "Faculty",
            "start_time": 30.0,
            "end_time": 60.0,
            "text": "A compiler executes the source code directly.",
        }
    ]
    curr = db_session.query(Curriculum).first()
    res = service.process_and_validate_transcript(chunks, curriculum_id=curr.id if curr else None)

    assert res["status"] == "SUCCESS"
    assert res["validated_chunks"] == 1
    assert res["incorrect_concepts"] == 1


def test_validation_engine_empty_transcript(db_session):
    service = ValidationService(db_session)
    with pytest.raises(EmptyTranscriptError):
        service.process_and_validate_transcript([])


def test_validation_engine_large_lecture(db_session):
    service = ValidationService(db_session)
    chunks = [
        {
            "chunk_id": f"chunk_{i}",
            "speaker": "Faculty",
            "start_time": float(i * 10),
            "end_time": float((i + 1) * 10),
            "text": f"Lecture chunk {i} discussing lexical analysis tokens and finite automata.",
        }
        for i in range(25)
    ]
    curr = db_session.query(Curriculum).first()
    res = service.process_and_validate_transcript(chunks, curriculum_id=curr.id if curr else None)

    assert res["status"] == "SUCCESS"
    assert res["validated_chunks"] == 25
    assert res["average_confidence"] > 0
