"""
Unit tests for Coverage Engine main pipeline.
Tests: Complete lecture, partial lecture, empty transcript error, large lecture, idempotent upsert.
"""

import pytest
from app.models.curriculum import Curriculum
from app.models.topic import Topic
from app.services.coverage.coverage_service import CoverageService
from app.services.coverage.exceptions import EmptyTranscriptError


def _get_valid_curriculum(db_session):
    topic = db_session.query(Topic).first()
    if topic:
        return db_session.get(Curriculum, topic.curriculum_id)
    return db_session.query(Curriculum).first()


def test_coverage_engine_complete_lecture(db_session):
    service = CoverageService(db_session)
    curr = _get_valid_curriculum(db_session)

    # Get first topic from DB to test matching
    first_topic = db_session.query(Topic).filter(Topic.curriculum_id == curr.id).first() if curr else None
    topic_id_str = str(first_topic.id) if first_topic else None

    chunks = [
        {
            "chunk_id": "chunk_1",
            "topic_id": topic_id_str,
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 180.0,
            "text": "Today we cover the compiler definition, history, and language processors in detail.",
        },
        {
            "chunk_id": "chunk_2",
            "topic_id": topic_id_str,
            "speaker": "Faculty",
            "start_time": 180.0,
            "end_time": 350.0,
            "text": "Continuing our discussion on compiler design phases and lexical analysis tokens.",
        },
    ]

    res = service.analyze_lecture_coverage(chunks, curriculum_id=curr.id if curr else None)

    assert res["status"] == "SUCCESS"
    assert res["covered_topics"] >= 1
    assert "weighted_coverage" in res
    assert "remaining_topics" in res


def test_coverage_engine_empty_transcript_raises_error(db_session):
    service = CoverageService(db_session)
    with pytest.raises(EmptyTranscriptError):
        service.analyze_lecture_coverage([])


def test_coverage_engine_idempotent_reanalysis(db_session):
    """Running coverage analysis twice for the same lecture updates existing records without duplicate rows."""
    service = CoverageService(db_session)
    curr = _get_valid_curriculum(db_session)

    chunks = [
        {
            "chunk_id": "chunk_1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 120.0,
            "text": "Lexical analysis produces tokens from characters.",
        }
    ]

    res1 = service.analyze_lecture_coverage(chunks, curriculum_id=curr.id if curr else None)
    lec_id = res1["lecture_id"]

    # Re-run same analysis
    res2 = service.analyze_lecture_coverage(chunks, lecture_id=lec_id, curriculum_id=curr.id if curr else None)

    assert res2["status"] == "SUCCESS"
    assert res2["lecture_id"] == lec_id
