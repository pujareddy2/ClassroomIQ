"""
Integration tests for Teaching Intelligence REST APIs.
Endpoints:
  POST /api/v1/teaching/analyze
  GET  /api/v1/teaching/{lecture_id}
  GET  /api/v1/teaching/{lecture_id}/summary
  GET  /api/v1/teaching/{lecture_id}/strengths
  GET  /api/v1/teaching/{lecture_id}/weaknesses
  GET  /api/v1/teaching/{lecture_id}/examples
  GET  /api/v1/teaching/{lecture_id}/interaction
  GET  /api/v1/teaching/{lecture_id}/structure
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_LECTURE_ID = str(uuid.uuid4())
SAMPLE_CURRICULUM_ID = str(uuid.uuid4())

SAMPLE_ANALYZE_PAYLOAD = {
    "lecture_id": SAMPLE_LECTURE_ID,
    "curriculum_id": SAMPLE_CURRICULUM_ID,
    "transcript_chunks": [
        {
            "chunk_id": "c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 60.0,
            "text": "Welcome class! Today we will define recursion. A recursive function is defined as a function that calls itself.",
        },
        {
            "chunk_id": "c2",
            "speaker": "Faculty",
            "start_time": 60.0,
            "end_time": 120.0,
            "text": "For example, in real life, binary tree traversal uses recursion.",
        },
        {
            "chunk_id": "c3",
            "speaker": "Faculty",
            "start_time": 120.0,
            "end_time": 180.0,
            "text": "Does anyone have any questions? Is that clear?",
        },
        {
            "chunk_id": "c4",
            "speaker": "Faculty",
            "start_time": 180.0,
            "end_time": 240.0,
            "text": "To summarize, today we covered base cases and recursive steps in algorithms.",
        },
    ],
}


def test_teaching_analyze_api_flow():
    # 1. POST /api/v1/teaching/analyze
    res = client.post("/api/v1/teaching/analyze", json=SAMPLE_ANALYZE_PAYLOAD)
    assert res.status_code == 201, res.text
    envelope = res.json()

    assert envelope["status"] == "SUCCESS"
    assert "data" in envelope
    data = envelope["data"]

    assert data["lecture_id"] == SAMPLE_LECTURE_ID
    assert data["teaching_score"] > 0
    assert data["grade"] in ["A+", "A", "B", "C", "D"]
    assert data["analysis_reused"] is False

    # 2. Duplicate POST /api/v1/teaching/analyze (Idempotency test)
    res_dup = client.post("/api/v1/teaching/analyze", json=SAMPLE_ANALYZE_PAYLOAD)
    assert res_dup.status_code == 201
    data_dup = res_dup.json()["data"]
    assert data_dup["analysis_reused"] is True

    # 3. GET /api/v1/teaching/{lecture_id}
    res_full = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}")
    assert res_full.status_code == 200
    assert res_full.json()["data"]["teaching_score"] == data["teaching_score"]

    # 4. GET /api/v1/teaching/{lecture_id}/summary
    res_sum = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}/summary")
    assert res_sum.status_code == 200
    assert "teaching_score" in res_sum.json()["data"]

    # 5. GET /api/v1/teaching/{lecture_id}/strengths
    res_str = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}/strengths")
    assert res_str.status_code == 200
    assert len(res_str.json()["data"]["strengths"]) >= 1

    # 6. GET /api/v1/teaching/{lecture_id}/weaknesses
    res_wk = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}/weaknesses")
    assert res_wk.status_code == 200

    # 7. GET /api/v1/teaching/{lecture_id}/examples
    res_ex = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}/examples")
    assert res_ex.status_code == 200
    assert res_ex.json()["data"]["example_count"] >= 1

    # 8. GET /api/v1/teaching/{lecture_id}/interaction
    res_in = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}/interaction")
    assert res_in.status_code == 200
    assert res_in.json()["data"]["engagement_opportunities"] >= 1

    # 9. GET /api/v1/teaching/{lecture_id}/structure
    res_st = client.get(f"/api/v1/teaching/{SAMPLE_LECTURE_ID}/structure")
    assert res_st.status_code == 200
    assert res_st.json()["data"]["has_introduction"] is True
    assert res_st.json()["data"]["has_conclusion"] is True


def test_teaching_api_not_found():
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/v1/teaching/{fake_id}")
    assert res.status_code == 404
