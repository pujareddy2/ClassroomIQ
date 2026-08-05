"""
Integration tests for Recommendation Engine REST APIs (/api/v1/recommendations/*).
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_recommendation_api_pipeline():
    lec_id = str(uuid.uuid4())
    fac_id = str(uuid.uuid4())

    # 1. POST /api/v1/recommendations/generate
    payload = {
        "lecture_id": lec_id,
        "faculty_id": fac_id,
        "force_reanalyze": True,
    }
    res = client.post("/api/v1/recommendations/generate", json=payload)
    assert res.status_code == 201, res.text
    env = res.json()
    assert env["status"] == "SUCCESS"
    data = env["data"]
    assert data["lecture_id"] == lec_id
    assert "total_recommendations" in data

    # 2. GET /api/v1/recommendations/{lecture_id}
    res_get = client.get(f"/api/v1/recommendations/{lec_id}")
    assert res_get.status_code == 200
    env_get = res_get.json()
    assert env_get["status"] == "SUCCESS"
    assert env_get["data"]["lecture_id"] == lec_id

    # 3. GET /api/v1/recommendations/{lecture_id}/priority
    res_prio = client.get(f"/api/v1/recommendations/{lec_id}/priority")
    assert res_prio.status_code == 200
    env_prio = res_prio.json()
    assert env_prio["status"] == "SUCCESS"
    assert isinstance(env_prio["data"], list)

    # 4. GET /api/v1/recommendations/{lecture_id}/evidence
    res_ev = client.get(f"/api/v1/recommendations/{lec_id}/evidence")
    assert res_ev.status_code == 200
    env_ev = res_ev.json()
    assert env_ev["status"] == "SUCCESS"
    assert isinstance(env_ev["data"], list)

    # 5. GET /api/v1/recommendations/faculty/{faculty_id}/weekly
    res_w = client.get(f"/api/v1/recommendations/faculty/{fac_id}/weekly?week_label=2026-W31")
    assert res_w.status_code == 200
    env_w = res_w.json()
    assert env_w["status"] == "SUCCESS"
    assert env_w["data"]["faculty_id"] == fac_id

    # 6. GET /api/v1/recommendations/faculty/{faculty_id}/monthly
    res_m = client.get(f"/api/v1/recommendations/faculty/{fac_id}/monthly?month_label=2026-08")
    assert res_m.status_code == 200
    env_m = res_m.json()
    assert env_m["status"] == "SUCCESS"
    assert env_m["data"]["faculty_id"] == fac_id

    # 7. GET /api/v1/recommendations/faculty/{faculty_id}/history
    res_h = client.get(f"/api/v1/recommendations/faculty/{fac_id}/history")
    assert res_h.status_code == 200
    env_h = res_h.json()
    assert env_h["status"] == "SUCCESS"
    assert isinstance(env_h["data"], list)


def test_recommendation_idempotency():
    lec_id = str(uuid.uuid4())
    fac_id = str(uuid.uuid4())
    payload = {
        "lecture_id": lec_id,
        "faculty_id": fac_id,
        "force_reanalyze": False,
    }

    # First call -> generates new
    res1 = client.post("/api/v1/recommendations/generate", json=payload)
    assert res1.status_code == 201
    d1 = res1.json()["data"]

    # Second call -> reused from cache
    res2 = client.post("/api/v1/recommendations/generate", json=payload)
    assert res2.status_code == 201
    d2 = res2.json()["data"]
    assert d2["analysis_reused"] is True
