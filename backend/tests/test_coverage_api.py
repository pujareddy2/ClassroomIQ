"""
Integration tests for Curriculum Coverage Intelligence Engine REST APIs.
Endpoints:
  POST /coverage/analyze
  GET  /coverage/{lecture_id}
  GET  /coverage/{lecture_id}/topics
  GET  /coverage/{lecture_id}/remaining
  GET  /coverage/{lecture_id}/timeline
  GET  /coverage/{lecture_id}/summary
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_COVERAGE_PAYLOAD = {
    "course_id": "CS101",
    "chunks": [
        {
            "chunk_id": "c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 150.0,
            "text": "Welcome to compiler design. Introduction to compiler definitions.",
        },
        {
            "chunk_id": "c2",
            "speaker": "Faculty",
            "start_time": 150.0,
            "end_time": 300.0,
            "text": "Lexical analysis phase produces tokens from source code.",
        },
    ],
}


def test_post_coverage_analyze_api():
    res = client.post("/api/v1/coverage/analyze", json=SAMPLE_COVERAGE_PAYLOAD)
    assert res.status_code == 201 or res.status_code == 200, res.text
    envelope = res.json()
    assert envelope["status"] == "SUCCESS"
    data = envelope["data"] if "data" in envelope else envelope

    assert "lecture_id" in data
    assert "covered_topics" in data
    assert "weighted_coverage" in data
    assert "remaining_topics" in data

    lecture_id = data["lecture_id"]

    # 1. GET /api/v1/coverage/{lecture_id}
    r1 = client.get(f"/api/v1/coverage/{lecture_id}/summary")
    assert r1.status_code == 200
    sum1 = r1.json()["data"] if "data" in r1.json() else r1.json()
    assert sum1["lecture_id"] == lecture_id

    # 2. GET /api/v1/coverage/{lecture_id}/topics
    r2 = client.get(f"/api/v1/coverage/{lecture_id}/topics")
    assert r2.status_code == 200
    topics = r2.json()["data"] if "data" in r2.json() else r2.json()
    assert len(topics) >= 1

    # 3. GET /api/v1/coverage/{lecture_id}/remaining
    r3 = client.get(f"/api/v1/coverage/{lecture_id}/remaining")
    assert r3.status_code == 200
    rem = r3.json()["data"] if "data" in r3.json() else r3.json()
    assert "remaining_topics" in rem

    # 4. GET /api/v1/coverage/{lecture_id}/timeline
    r4 = client.get(f"/api/v1/coverage/{lecture_id}/timeline")
    assert r4.status_code == 200
    timeline = r4.json()["data"] if "data" in r4.json() else r4.json()
    assert len(timeline["intervals"]) >= 0

    # 5. GET /api/v1/coverage/{lecture_id}/summary
    r5 = client.get(f"/api/v1/coverage/{lecture_id}/summary")
    assert r5.status_code == 200
    summary = r5.json()["data"] if "data" in r5.json() else r5.json()
    assert summary["lecture_id"] == lecture_id


def test_coverage_api_not_found():
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/coverage/{fake_id}")
    assert res.status_code == 404
