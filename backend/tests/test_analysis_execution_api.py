"""Contract tests for the centralized AI execution polling API."""

import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analysis_status_is_non_error_before_a_job_exists():
    lecture_id = uuid.uuid4()
    response = client.get(f"/api/v1/analysis/status/{lecture_id}")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "SUCCESS"
    assert payload["data"]["lecture_id"] == str(lecture_id)
    assert payload["data"]["overall_status"] == "NOT_STARTED"
    assert payload["data"]["progress_percentage"] == 0


def test_analysis_run_requires_lecture_and_curriculum_ids():
    response = client.post("/api/v1/analysis/run", json={})
    assert response.status_code == 422
    assert response.json()["status"] == "ERROR"
