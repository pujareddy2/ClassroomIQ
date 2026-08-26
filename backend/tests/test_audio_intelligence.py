"""
Unit and Integration tests for Audio Intelligence, Whisper STT, and Diarization (Module 2).
"""

import io
import wave
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.audio.diarization_engine import DiarizationEngine
from app.services.audio.vad_service import VADService
from app.services.audio.whisper_engine import WhisperEngine

client = TestClient(app)


def _generate_wav_file(duration_sec: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generates valid 16kHz mono PCM WAV bytes with mock audio bursts."""
    buf = io.BytesIO()
    num_frames = int(sample_rate * duration_sec)
    # Generate alternating bursts of audio signal and silence
    samples = []
    for i in range(num_frames):
        # 1-second burst followed by silence
        if (i % sample_rate) < (sample_rate * 0.7):
            val = int(8000 * (1 if (i % 20) < 10 else -1))
        else:
            val = 0
        samples.append(val)

    import struct
    raw_data = struct.pack(f"<{len(samples)}h", *samples)

    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_data)

    return buf.getvalue()


def test_vad_service(tmp_path):
    """Tests Voice Activity Detection identifying active speech intervals."""
    vad = VADService(energy_threshold=0.01)
    audio_path = tmp_path / "lecture_audio.wav"
    audio_path.write_bytes(_generate_wav_file(duration_sec=3.0))

    intervals = vad.detect_speech_intervals(audio_path)
    assert len(intervals) >= 1
    assert intervals[0].duration_sec > 0
    assert intervals[0].start_sec >= 0.0


def test_whisper_engine_with_domain_vocabulary(tmp_path):
    """Tests Whisper transcription engine with academic domain vocabulary."""
    whisper = WhisperEngine()
    audio_path = tmp_path / "cs_lecture.wav"
    audio_path.write_bytes(_generate_wav_file(duration_sec=20.0))

    custom_vocab = ["AVL Trees", "Rotations", "Balance Factor"]
    segments = whisper.transcribe_audio(audio_path, domain_vocabulary=custom_vocab)

    assert len(segments) >= 1
    assert segments[0]["start"] >= 0.0
    assert segments[0]["end"] > segments[0]["start"]
    assert "text" in segments[0]


def test_diarization_teacher_vs_student():
    """Tests speaker diarization separating Teacher explanation from Student question."""
    engine = DiarizationEngine()
    mock_transcript = [
        {"text": "Welcome class. Today we will explore binary search trees and logarithmic search.", "start": 0.0, "end": 10.0},
        {"text": "Excuse me professor, why does an unbalanced tree degrade into O(n)?", "start": 10.5, "end": 15.0},
        {"text": "Great question. Because all nodes are inserted in sorted order without rebalancing.", "start": 15.5, "end": 25.0},
    ]

    segments, summary = engine.diarize_segments(mock_transcript)

    assert len(segments) == 3
    assert segments[0].speaker == "Teacher"
    assert segments[1].speaker == "Student"  # Detected question indicator
    assert segments[2].speaker == "Teacher"

    assert summary.teacher_segments == 2
    assert summary.student_segments == 1
    assert summary.teacher_talk_ratio > 0.6


def test_audio_process_session_api():
    """Full integration test: Upload lecture -> Run Audio Intelligence -> Get Transcript."""
    # 1. Upload lecture with audio
    wav_bytes = _generate_wav_file(duration_sec=15.0)
    files = {"audio_file": ("audio_analysis_lecture.wav", wav_bytes, "audio/wav")}
    form_data = {
        "course_name_or_code": "CS301 - Operating Systems",
        "faculty_name": "Dr. Linus Torvalds",
        "title": "Process Scheduling & Deadlocks",
        "classroom": "Hall 4",
    }
    up_res = client.post("/api/v1/multimedia/upload", data=form_data, files=files)
    assert up_res.status_code == 201, up_res.text
    session_id = up_res.json()["data"]["session_id"]

    # 2. Trigger Audio Processing pipeline
    process_payload = {
        "domain_vocabulary": ["Semaphores", "Mutex", "Deadlock Prevention"],
        "enable_vad": True,
        "enable_diarization": True,
        "sync_academic": True,
    }
    proc_res = client.post(f"/api/v1/audio/session/{session_id}/process-sync", json=process_payload)
    assert proc_res.status_code == 200, proc_res.text
    proc_data = proc_res.json()["data"]

    assert proc_data["status"] == "COMPLETED"
    assert proc_data["total_segments"] >= 1
    assert proc_data["total_words"] > 0
    assert "diarization_summary" in proc_data
    assert proc_data["diarization_summary"]["teacher_talk_ratio"] >= 0.0

    # 3. Retrieve Transcript via GET API
    t_res = client.get(f"/api/v1/audio/session/{session_id}/transcript")
    assert t_res.status_code == 200
    t_data = t_res.json()["data"]
    assert t_data["has_transcript"] is True
    assert len(t_data["segments"]) >= 1
    assert t_data["segments"][0]["speaker"] in {"Teacher", "Student"}


def test_standalone_transcribe_file_api():
    """Tests direct transcription endpoint for raw audio uploads."""
    wav_bytes = _generate_wav_file(duration_sec=5.0)
    files = {"audio_file": ("standalone_test.wav", wav_bytes, "audio/wav")}
    res = client.post("/api/v1/audio/transcribe-file", files=files)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "segments" in data
    assert len(data["segments"]) >= 1
