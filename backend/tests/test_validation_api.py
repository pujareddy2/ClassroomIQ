"""
Integration tests for Technical Validation Engine REST APIs.
Endpoints:
  POST /validation/analyze
  GET  /validation/{lecture_id}
  GET  /validation/{lecture_id}/summary
  GET  /validation/{lecture_id}/evidence
  GET  /validation/{lecture_id}/timeline
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_TRANSCRIPT_PAYLOAD = {
    "course_id": "CS101",
    "transcript_chunks": [
        {
            "chunk_id": "c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 40.0,
            "text": "A compiler is a program that translates high level source code into machine code.",
        },
        {
            "chunk_id": "c2",
            "speaker": "Faculty",
            "start_time": 40.0,
            "end_time": 80.0,
            "text": "A compiler executes the source code directly.",
        },
        {
            "chunk_id": "c3",
            "speaker": "Faculty",
            "start_time": 80.0,
            "end_time": 120.0,
            "text": "Bubble sort has an average time complexity of O(1).",
        },
    ],
}


def test_post_validation_analyze():
    res = client.post("/api/v1/validation/analyze", json=SAMPLE_TRANSCRIPT_PAYLOAD)
    assert res.status_code == 200, res.text
    envelope = res.json()
    assert envelope["status"] == "SUCCESS"
    data = envelope["data"]
    assert data["validated_chunks"] == 3
    assert data["correct_concepts"] >= 1
    assert data["incorrect_concepts"] >= 1
    assert data["formula_issues"] >= 1
    assert "overall_validation_score" in data
    assert "lecture_quality" in data
    assert "validation_percentage" in data

    lecture_id = data["lecture_id"]

    # Test GET /api/v1/validation/{lecture_id}
    r2 = client.get(f"/api/v1/validation/{lecture_id}")
    assert r2.status_code == 200
    items = r2.json()["data"]
    assert len(items) == 3
    assert "category" in items[0]
    assert "validation_status" in items[0]

    # Test GET /api/v1/validation/{lecture_id}/summary
    r3 = client.get(f"/api/v1/validation/{lecture_id}/summary")
    assert r3.status_code == 200
    summary = r3.json()["data"]
    assert summary["validated_chunks"] == 3
    assert "overall_validation_score" in summary
    assert "lecture_quality" in summary

    # Test GET /api/v1/validation/{lecture_id}/evidence
    r4 = client.get(f"/api/v1/validation/{lecture_id}/evidence")
    assert r4.status_code == 200
    evidence = r4.json()["data"]
    assert len(evidence) >= 1

    # Test GET /api/v1/validation/{lecture_id}/timeline
    r5 = client.get(f"/api/v1/validation/{lecture_id}/timeline")
    assert r5.status_code == 200
    timeline = r5.json()["data"]
    assert len(timeline["intervals"]) == 3
    assert timeline["intervals"][0]["start_time"] == 0.0
    assert "status" in timeline["intervals"][0]
    assert "category" in timeline["intervals"][0]


def test_validation_api_not_found():
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/validation/{fake_id}")
    assert res.status_code == 404
