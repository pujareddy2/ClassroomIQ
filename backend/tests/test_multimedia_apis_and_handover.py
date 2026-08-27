"""
Automated unit & integration tests for Member 1 Module 5 (Multimedia APIs & Handover Contract).
"""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.multimedia.storage_service import MultimediaStorageService

client = TestClient(app)


def test_handover_contract_api():
    """Verifies that Member 1 Handover Contract endpoint returns structured contract data for Member 2."""
    session_id = uuid4()
    storage = MultimediaStorageService()
    dirs = storage.get_session_paths(session_id)

    # Create dummy raw video file
    video_file = dirs["raw"] / "test_lecture.mp4"
    video_file.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"\x00" * 200)

    try:
        response = client.get(f"/api/v1/multimedia/handover-contract/{session_id}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "SUCCESS"
        data = payload["data"]
        assert "session_id" in data
        assert "transcript_segments" in data
        assert "visual_events" in data
        assert "topic_segments" in data
        assert "synchronized_timeline" in data
        assert "metadata" in data
    finally:
        storage.delete_session_dir(session_id)


def test_session_export_api():
    """Verifies complete session JSON package download."""
    session_id = uuid4()
    storage = MultimediaStorageService()
    dirs = storage.get_session_paths(session_id)

    video_file = dirs["raw"] / "test_lecture.mp4"
    video_file.write_bytes(b"\x00\x00\x00\x18ftypisom" + b"\x00" * 100)

    try:
        response = client.get(f"/api/v1/multimedia/session/{session_id}/export")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        body = response.json()
        data = body.get("data", body)
        assert "metadata" in data
        assert "structuring" in data

    finally:
        storage.delete_session_dir(session_id)


def test_stream_media_range_requests():
    """Verifies HTTP Range partial content responses (206) for video seeking."""
    session_id = uuid4()
    storage = MultimediaStorageService()
    dirs = storage.get_session_paths(session_id)

    dummy_video = dirs["raw"] / "video.mp4"
    content = b"0123456789" * 100  # 1000 bytes
    dummy_video.write_bytes(content)

    try:
        # Full request
        resp_full = client.get(f"/api/v1/multimedia/session/{session_id}/stream?media_type=video")
        assert resp_full.status_code == 200

        # Partial Range request
        resp_range = client.get(
            f"/api/v1/multimedia/session/{session_id}/stream?media_type=video",
            headers={"Range": "bytes=0-99"},
        )
        assert resp_range.status_code == 206
        assert resp_range.headers["Content-Range"] == "bytes 0-99/1000"
        assert resp_range.headers["Content-Length"] == "100"
        assert len(resp_range.content) == 100
    finally:
        storage.delete_session_dir(session_id)
