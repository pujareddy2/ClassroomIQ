"""
Unit and Integration tests for Video Intelligence, OpenCV Pipeline, and Visual Timeline (Module 3).
"""

import io
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.video import DetectionBox, SceneType, VideoFrameAnalysis, VideoProcessRequest
from app.services.video.board_detector import BoardDetector
from app.services.video.frame_extractor import FrameExtractor
from app.services.video.ppt_detector import PPTDetector
from app.services.video.scene_classifier import SceneClassifier
from app.services.video.teacher_detector import TeacherDetector
from app.services.video.video_intelligence_service import VideoIntelligenceService

client = TestClient(app)


def _generate_synthetic_video(file_path: Path, duration_sec: float = 6.0, fps: float = 10.0) -> Path:
    """Generates a synthetic MP4 video file with changing visual teaching scenes."""
    width, height = 640, 360
    total_frames = int(duration_sec * fps)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(file_path), fourcc, fps, (width, height))

    for i in range(total_frames):
        frame = np.full((height, width, 3), 40, dtype=np.uint8)

        # First third: Teacher lecturing at podium
        if i < total_frames // 3:
            # Draw instructor (head + body)
            cv2.circle(frame, (160, 100), 25, (180, 180, 200), -1)
            cv2.rectangle(frame, (130, 130), (190, 280), (100, 120, 220), -1)
            # Draw podium
            cv2.rectangle(frame, (110, 220), (210, 340), (80, 60, 40), -1)

        # Second third: Active board writing
        elif i < (2 * total_frames) // 3:
            # Draw large dark chalkboard
            cv2.rectangle(frame, (80, 40), (560, 300), (20, 50, 30), -1)
            # Draw chalk strokes / math formulas
            cv2.putText(frame, "f(x) = O(log n)", (120, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (240, 240, 240), 2)
            cv2.putText(frame, "E = mc^2", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (240, 240, 240), 2)
            # Instructor hand/body near board
            cv2.rectangle(frame, (380, 100), (450, 320), (120, 140, 200), -1)

        # Last third: Bright PPT presentation screen
        else:
            # Draw 16:9 projection screen
            cv2.rectangle(frame, (100, 30), (540, 290), (245, 245, 245), -1)
            cv2.putText(frame, "SLIDE: ALGORITHMS", (130, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
            cv2.putText(frame, "1. Binary Search", (130, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)
            cv2.putText(frame, "2. AVL Tree Rotations", (130, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)

        out.write(frame)

    out.release()
    return file_path


def test_frame_extractor(tmp_path):
    """Tests OpenCV frame sampling, keyframe saving, and scene transition difference."""
    video_path = tmp_path / "test_lecture.mp4"
    _generate_synthetic_video(video_path, duration_sec=4.0, fps=10.0)

    extractor = FrameExtractor(target_width=640, target_height=360)
    frames = extractor.extract_sampled_frames(video_path, sample_interval_sec=1.0)

    assert len(frames) >= 3
    assert frames[0][0] == 0.0
    assert frames[0][1].shape == (360, 640, 3)

    # Test scene change score
    diff = extractor.compute_scene_change_score(frames[0][1], frames[-1][1])
    assert diff > 0.1  # Distinct scenes should have noticeable difference

    # Test keyframe save
    keyframe_dir = tmp_path / "keyframes"
    saved = extractor.save_keyframe(frames[0][1], keyframe_dir, "frame_001.jpg")
    assert saved.exists()
    assert saved.stat().st_size > 0


def test_teacher_detector():
    """Tests teacher detection and stage zone classification."""
    detector = TeacherDetector()
    frame = np.full((360, 640, 3), 50, dtype=np.uint8)

    # Draw person on left podium zone
    cv2.circle(frame, (140, 90), 25, (200, 200, 200), -1)
    cv2.rectangle(frame, (110, 120), (170, 290), (120, 140, 240), -1)

    is_detected, box, zone = detector.detect_teacher(frame)
    assert is_detected is True
    assert box is not None
    assert box.w > 0
    assert box.h > 0
    assert zone in {"board_left", "podium", "center"}


def test_board_detector():
    """Tests whiteboard/blackboard detection and stroke writing density calculation."""
    detector = BoardDetector()
    frame = np.full((360, 640, 3), 40, dtype=np.uint8)

    # Draw large board with dense text strokes
    cv2.rectangle(frame, (60, 30), (580, 310), (15, 45, 25), -1)
    for y_pos in [80, 130, 180, 230]:
        cv2.putText(frame, "Calculus Theorem: f'(x) = lim (f(x+h)-f(x))/h", (80, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    is_board, box, stroke_pct = detector.detect_board(frame)
    assert is_board is True
    assert box is not None
    assert stroke_pct > 1.0


def test_ppt_detector():
    """Tests digital slide detection and transition detection."""
    detector = PPTDetector()

    # Frame 1: Slide A
    frame1 = np.full((360, 640, 3), 30, dtype=np.uint8)
    cv2.rectangle(frame1, (100, 30), (540, 290), (250, 250, 250), -1)
    cv2.putText(frame1, "Slide 1: Introduction", (140, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    is_ppt, box, is_transition = detector.detect_ppt(frame1)
    assert is_ppt is True
    assert box is not None

    # Frame 2: Slide B (Transition should trigger)
    frame2 = np.full((360, 640, 3), 30, dtype=np.uint8)
    cv2.rectangle(frame2, (100, 30), (540, 290), (250, 250, 250), -1)
    cv2.putText(frame2, "Slide 2: System Architecture Diagram", (120, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.rectangle(frame2, (150, 160), (480, 260), (50, 50, 50), -1)

    is_ppt2, box2, is_transition2 = detector.detect_ppt(frame2)
    assert is_ppt2 is True
    assert is_transition2 is True


def test_scene_classifier_and_timeline():
    """Tests multi-modal scene classification and chronological visual timeline event clustering."""
    classifier = SceneClassifier()

    analyses = [
        VideoFrameAnalysis(
            timestamp_sec=0.0,
            scene_type=SceneType.TEACHER_LECTURING,
            teacher_detected=True,
            teacher_zone="podium",
            keyframe_filename="key_001.jpg",
        ),
        VideoFrameAnalysis(
            timestamp_sec=5.0,
            scene_type=SceneType.TEACHER_LECTURING,
            teacher_detected=True,
            teacher_zone="center",
            keyframe_filename="key_002.jpg",
        ),
        VideoFrameAnalysis(
            timestamp_sec=10.0,
            scene_type=SceneType.BOARD_WRITING,
            board_detected=True,
            stroke_density=4.5,
            keyframe_filename="key_003.jpg",
        ),
        VideoFrameAnalysis(
            timestamp_sec=15.0,
            scene_type=SceneType.PPT_PRESENTATION,
            ppt_detected=True,
            keyframe_filename="key_004.jpg",
        ),
    ]

    events = classifier.generate_timeline_events(analyses, min_event_duration_sec=3.0)
    assert len(events) >= 3
    assert events[0].scene_type == SceneType.TEACHER_LECTURING
    assert events[0].start_time_sec == 0.0
    assert events[0].end_time_sec >= 5.0
    assert events[0].duration_sec > 0


def test_standalone_video_analyze_api(tmp_path):
    """Tests the POST /api/v1/video/analyze-file endpoint with direct video upload."""
    video_path = tmp_path / "api_test_video.mp4"
    _generate_synthetic_video(video_path, duration_sec=5.0, fps=10.0)

    video_bytes = video_path.read_bytes()
    files = {"video_file": ("test_lecture.mp4", video_bytes, "video/mp4")}
    data = {
        "sample_interval_sec": 1.5,
        "detect_teacher": True,
        "detect_board": True,
        "detect_ppt": True,
    }

    res = client.post("/api/v1/video/analyze-file", files=files, data=data)
    assert res.status_code == 200, res.text

    payload = res.json()
    data_obj = payload.get("data", payload)

    assert data_obj["status"] == "COMPLETED"
    assert "summary" in data_obj
    assert "timeline" in data_obj
    assert "keyframes" in data_obj
    assert data_obj["summary"]["analyzed_frames_count"] >= 3
    assert len(data_obj["timeline"]) >= 1
