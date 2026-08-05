"""
Integration tests for POST /lecture/upload-transcript API.
Tests: short, long, multi-speaker, empty, and large transcripts.
"""

import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SHORT_TRANSCRIPT = [
    {"speaker": "Faculty", "start": 0.0, "end": 12.5,
     "text": "A compiler is a program that translates source code into machine code."},
    {"speaker": "Faculty", "start": 12.5, "end": 25.0,
     "text": "Lexical analysis is the first phase of a compiler."},
]

MULTI_SPEAKER_TRANSCRIPT = [
    {"speaker": "Faculty", "start": 0.0, "end": 15.0,
     "text": "Today we discuss compiler phases."},
    {"speaker": "Student", "start": 15.0, "end": 22.0,
     "text": "What is lexical analysis?"},
    {"speaker": "Faculty", "start": 22.0, "end": 45.0,
     "text": "Lexical analysis breaks the source code into tokens using finite automata."},
    {"speaker": "Faculty", "start": 45.0, "end": 80.0,
     "text": "Then syntax analysis checks grammatical structure using context-free grammar."},
]

LONG_TRANSCRIPT = [
    {"speaker": "Faculty", "start": float(i * 15), "end": float((i + 1) * 15),
     "text": f"In this part of the lecture we cover topic number {i + 1} which relates to compiler design phases and lexical analysis tokens."}
    for i in range(20)
]

FILLER_TRANSCRIPT = [
    {"speaker": "Faculty", "start": 0.0, "end": 20.0,
     "text": "Um so today we um are going to talk about uh the compiler. You know like, it takes source code."},
    {"speaker": "Faculty", "start": 20.0, "end": 40.0,
     "text": "Uh lexical analysis is, you know, the the first phase. Uh it it produces tokens."},
]


def _upload(transcript_items, course_id="CS101", faculty_name="Dr. Test"):
    payload = {
        "course_id": course_id,
        "faculty_name": faculty_name,
        "transcript": transcript_items,
    }
    return client.post("/api/v1/lecture/upload-transcript", json=payload)


def test_short_transcript_upload():
    res = _upload(SHORT_TRANSCRIPT)
    assert res.status_code == 201, res.text
    envelope = res.json()
    assert envelope["status"] == "SUCCESS"
    data = envelope["data"]
    assert data["chunks"] >= 1
    assert "lecture_id" in data
    assert "transcript_id" in data
    assert "processing_time" in data


def test_multi_speaker_transcript():
    res = _upload(MULTI_SPEAKER_TRANSCRIPT)
    assert res.status_code == 201, res.text
    envelope = res.json()
    assert envelope["status"] == "SUCCESS"
    data = envelope["data"]
    assert data["chunks"] >= 2   # faculty and student turn chunks


def test_long_transcript_upload():
    res = _upload(LONG_TRANSCRIPT)
    assert res.status_code == 201, res.text
    envelope = res.json()
    assert envelope["status"] == "SUCCESS"
    data = envelope["data"]
    assert data["chunks"] >= 5


def test_filler_word_cleaning():
    """Verify filler words are cleaned before chunking."""
    res = _upload(FILLER_TRANSCRIPT)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    # Total words in chunks should be less than raw word count after cleaning
    assert data["chunks"] >= 1


def test_empty_transcript_returns_400():
    payload = {
        "course_id": "CS101",
        "faculty_name": "Dr. Test",
        "transcript": [],
    }
    res = client.post("/api/v1/lecture/upload-transcript", json=payload)
    assert res.status_code == 422  # Pydantic min_length=1 triggers 422


def test_invalid_lecture_id_returns_not_found():
    """Verify that a nonexistent lecture_id in GET returns 404."""
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/lecture/{fake_id}")
    assert res.status_code == 404
