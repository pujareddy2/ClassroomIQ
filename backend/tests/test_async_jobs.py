"""
Tests for the Async Media Processing Job Queue system.
Covers job creation, status polling, and the /jobs API endpoints.
"""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.media_processing_job import MediaProcessingJob
from app.services.job_service import MediaJobService

client = TestClient(app)


def _upload_test_session() -> str:
    """Helper: uploads a minimal audio session and returns the session_id."""
    import io
    import struct
    import wave

    buf = io.BytesIO()
    num_frames = 16000 * 3  # 3s at 16kHz
    samples = [int(4000 * (1 if (i % 20) < 10 else -1)) for i in range(num_frames)]
    raw = struct.pack(f"<{len(samples)}h", *samples)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw)
    wav_bytes = buf.getvalue()

    files = {"audio_file": ("job_test.wav", wav_bytes, "audio/wav")}
    form = {
        "course_name_or_code": "CS999 - Job Queue Test",
        "faculty_name": "Dr. Queue",
        "title": "Async Test Lecture",
    }
    res = client.post("/api/v1/multimedia/upload", data=form, files=files)
    assert res.status_code == 201, res.text
    return res.json()["data"]["session_id"]


def test_async_audio_job_submit_returns_job_id():
    """POST /audio/session/{id}/process should return 202 + job_id immediately."""
    session_id = _upload_test_session()
    res = client.post(
        f"/api/v1/audio/session/{session_id}/process",
        json={"enable_vad": True, "enable_diarization": True},
    )
    assert res.status_code == 202, res.text
    data = res.json()["data"]
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["job_type"] == "audio_process"
    assert "/api/v1/jobs/" in data["poll_url"]
    # Validate job_id is a valid UUID
    UUID(data["job_id"])


def test_async_video_job_submit_returns_job_id():
    """POST /video/process/{id}/process should return 202 + job_id immediately."""
    session_id = _upload_test_session()
    res = client.post(
        f"/api/v1/video/process/{session_id}",
        json={"sample_interval_sec": 2.0},
    )
    assert res.status_code == 202, res.text
    data = res.json()["data"]
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["job_type"] == "video_process"


def test_job_status_polling_api():
    """GET /jobs/{job_id} should return the job's current state."""
    session_id = _upload_test_session()

    # Submit a job
    submit_res = client.post(f"/api/v1/audio/session/{session_id}/process", json={})
    assert submit_res.status_code == 202
    job_id = submit_res.json()["data"]["job_id"]

    # Poll the job status
    poll_res = client.get(f"/api/v1/jobs/{job_id}")
    assert poll_res.status_code == 200, poll_res.text
    job_data = poll_res.json()["data"]

    assert job_data["job_id"] == job_id
    assert job_data["status"] in {"PENDING", "RUNNING", "COMPLETED", "FAILED"}
    assert "progress" in job_data
    assert 0 <= job_data["progress"] <= 100


def test_job_status_404_for_unknown_job():
    """GET /jobs/{unknown_id} should return 404."""
    unknown_id = str(uuid4())
    res = client.get(f"/api/v1/jobs/{unknown_id}")
    assert res.status_code == 404


def test_list_session_jobs():
    """GET /jobs/session/{id} should list all jobs for a session."""
    session_id = _upload_test_session()

    # Submit two jobs
    client.post(f"/api/v1/audio/session/{session_id}/process", json={})
    client.post(f"/api/v1/audio/session/{session_id}/process", json={})

    res = client.get(f"/api/v1/jobs/session/{session_id}")
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["total"] >= 2
    assert len(data["jobs"]) >= 2
    # Jobs ordered newest first
    assert data["jobs"][0]["job_type"] == "audio_process"
