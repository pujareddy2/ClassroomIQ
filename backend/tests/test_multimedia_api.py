"""
Unit and Integration tests for Multimedia & Lecture Capture APIs (Module 1).
"""

import io
import wave
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.services.multimedia.ffmpeg_processor import FFmpegProcessor
from app.services.multimedia.storage_service import MultimediaStorageService

client = TestClient(app)


def _generate_mock_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Helper to generate in-memory valid WAV bytes."""
    buf = io.BytesIO()
    num_frames = int(sample_rate * duration_sec)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_frames)
    return buf.getvalue()


def test_live_session_full_lifecycle(tmp_path):
    """Tests Start -> Upload Chunks -> Complete -> Detail -> Stream pipeline."""
    # 1. Start Session
    start_payload = {
        "course_name_or_code": "CS101 - Intro to Programming",
        "faculty_name": "Dr. Alan Turing",
        "title": "Algorithms & Flowcharts",
        "classroom": "Hall A",
        "consent_confirmed": True,
        "has_screen_share": True,
    }
    res = client.post("/api/v1/multimedia/session/start", json=start_payload)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    session_id = data["session_id"]
    assert UUID(session_id)
    assert data["status"] == "RECORDING"

    # 2. Upload Chunks
    chunk_1 = b"\x00\x01\x02\x03" * 128
    chunk_2 = b"\x04\x05\x06\x07" * 128
    chunk_3 = _generate_mock_wav_bytes(duration_sec=0.5)

    res_c1 = client.post(
        f"/api/v1/multimedia/session/{session_id}/chunk",
        data={"chunk_index": 0},
        files={"chunk": ("chunk_0.part", chunk_1, "application/octet-stream")},
    )
    assert res_c1.status_code == 200
    assert res_c1.json()["data"]["status"] == "CHUNK_RECEIVED"

    res_c2 = client.post(
        f"/api/v1/multimedia/session/{session_id}/chunk",
        data={"chunk_index": 1},
        files={"chunk": ("chunk_1.part", chunk_2, "application/octet-stream")},
    )
    assert res_c2.status_code == 200

    res_c3 = client.post(
        f"/api/v1/multimedia/session/{session_id}/chunk",
        data={"chunk_index": 2},
        files={"chunk": ("chunk_2.part", chunk_3, "application/octet-stream")},
    )
    assert res_c3.status_code == 200
    assert res_c3.json()["data"]["total_chunks"] == 3

    # 3. Complete Session
    complete_res = client.post(
        f"/api/v1/multimedia/session/{session_id}/complete",
        json={"duration_seconds": 45.0, "notes": "Lecture finished cleanly."},
    )
    assert complete_res.status_code == 200
    comp_data = complete_res.json()["data"]
    assert comp_data["status"] == "ACTIVE"
    assert comp_data["duration_seconds"] == 45.0

    # 4. Get Session Detail
    detail_res = client.get(f"/api/v1/multimedia/session/{session_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert detail["session_id"] == session_id
    assert detail["status"] == "ACTIVE"


def test_upload_lecture_package():
    """Tests multipart upload with audio file and course metadata."""
    wav_bytes = _generate_mock_wav_bytes(duration_sec=2.0)
    files = {
        "audio_file": ("test_lecture.wav", wav_bytes, "audio/wav"),
    }
    form_data = {
        "course_name_or_code": "PHY201 - Quantum Mechanics",
        "faculty_name": "Dr. Richard Feynman",
        "title": "Wave Particle Duality",
        "classroom": "Physics Lab 2",
        "lecture_date": "2026-08-11",
    }
    res = client.post("/api/v1/multimedia/upload", data=form_data, files=files)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["course_name"]
    assert data["has_extracted_audio"] is True
    assert data["status"] == "ACTIVE"

    session_id = data["session_id"]

    # Verify session detail
    detail_res = client.get(f"/api/v1/multimedia/session/{session_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["audio_url"] is not None


def test_list_sessions():
    """Tests listing of recording sessions."""
    res = client.get("/api/v1/multimedia/sessions?limit=10")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


def test_multimedia_storage_service(tmp_path):
    """Unit test for storage service chunk saving and assembly."""
    storage = MultimediaStorageService(base_dir=tmp_path)
    session_id = UUID("11111111-2222-3333-4444-555555555555")

    dirs = storage.init_session_dir(session_id)
    assert dirs["root"].exists()
    assert dirs["chunks"].exists()

    storage.save_chunk(session_id, 0, b"Hello ")
    storage.save_chunk(session_id, 1, b"World!")
    assert storage.get_chunks_count(session_id) == 2

    assembled = storage.assemble_chunks(session_id, "output.txt")
    assert assembled.exists()
    assert assembled.read_text() == "Hello World!"


def test_ffmpeg_processor_wav_probe(tmp_path):
    """Unit test for WAV probing and 16k extraction fallback."""
    proc = FFmpegProcessor()
    wav_path = tmp_path / "test.wav"
    wav_bytes = _generate_mock_wav_bytes(duration_sec=1.5, sample_rate=16000)
    wav_path.write_bytes(wav_bytes)

    meta = proc.probe_media(wav_path)
    assert meta["has_audio"] is True
    assert meta["sample_rate"] == 16000
    assert meta["duration_seconds"] == 1.5

    out_16k = tmp_path / "extracted_16k.wav"
    extracted = proc.extract_audio_16k_mono(wav_path, out_16k)
    assert extracted.exists()
    assert extracted.stat().st_size > 0
