"""
Unit and Integration tests for Lecture Structuring, Media Synchronization & Handover Contract (Module 4).
"""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audio import TranscriptSegmentItem
from app.schemas.structuring import LectureStructureProcessRequest
from app.schemas.video import SceneType, VideoIntelligenceSummary, VisualTimelineEvent
from app.services.structuring.lecture_metadata_extractor import LectureMetadataExtractor
from app.services.structuring.lecture_structuring_service import LectureStructuringService
from app.services.structuring.media_synchronizer import MediaSynchronizer
from app.services.structuring.topic_segmenter import TopicSegmenter

client = TestClient(app)


def test_media_synchronizer():
    """Tests multi-track timeline alignment across speech, video scenes, and presentation slides."""
    synchronizer = MediaSynchronizer()

    transcripts = [
        TranscriptSegmentItem(start_time=0.0, end_time=10.0, speaker="Teacher", text="Welcome to Data Structures."),
        TranscriptSegmentItem(start_time=10.5, end_time=18.0, speaker="Student", text="Professor, what is the complexity of search?"),
        TranscriptSegmentItem(start_time=18.5, end_time=30.0, speaker="Teacher", text="Let's analyze binary search tree complexity on the board."),
    ]

    visuals = [
        VisualTimelineEvent(
            event_id="evt_01",
            start_time_sec=0.0,
            end_time_sec=15.0,
            duration_sec=15.0,
            scene_type=SceneType.TEACHER_LECTURING,
            label="Intro Lecturing",
            description="Teacher at podium",
        ),
        VisualTimelineEvent(
            event_id="evt_02",
            start_time_sec=15.0,
            end_time_sec=30.0,
            duration_sec=15.0,
            scene_type=SceneType.BOARD_WRITING,
            label="Board Work",
            description="Derivation on board",
        ),
    ]

    slides = [
        {"slide_number": 1, "title": "Course Overview: Trees", "text_content": "Introduction to binary search"},
        {"slide_number": 2, "title": "Complexity Analysis", "text_content": "O(log n) average case"},
    ]

    sync_points = synchronizer.build_synchronized_timeline(
        transcript_segments=transcripts,
        visual_events=visuals,
        slides=slides,
        total_duration_sec=30.0,
        resolution_sec=5.0,
    )

    assert len(sync_points) >= 6
    assert sync_points[0].timestamp_sec == 0.0
    assert sync_points[0].speaker == "Teacher"
    assert sync_points[0].visual_scene == SceneType.TEACHER_LECTURING
    assert sync_points[0].slide_number is not None

    # At t=25s, scene should be BOARD_WRITING
    point_25 = next(p for p in sync_points if p.timestamp_sec == 25.0)
    assert point_25.visual_scene == SceneType.BOARD_WRITING


def test_topic_segmenter():
    """Tests semantic topic segmentation and chapter generation from cue phrases."""
    segmenter = TopicSegmenter()

    transcripts = [
        TranscriptSegmentItem(start_time=0.0, end_time=20.0, speaker="Teacher", text="Today we will cover Binary Search Trees and tree invariants."),
        TranscriptSegmentItem(start_time=20.5, end_time=40.0, speaker="Teacher", text="Let's solve an example problem with AVL Tree Rotations and balance factors."),
        TranscriptSegmentItem(start_time=40.5, end_time=60.0, speaker="Teacher", text="To summarize, balancing prevents degenerate O(n) linked lists."),
    ]

    topics = segmenter.segment_lecture(transcript_segments=transcripts, min_segment_duration_sec=15.0)

    assert len(topics) >= 2
    assert topics[0].start_time_sec == 0.0
    assert topics[0].duration_sec >= 15.0
    assert len(topics[0].key_concepts) > 0
    assert topics[0].primary_speaker == "Teacher"


def test_lecture_metadata_extractor():
    """Tests speaking speed (WPM), pace categorization, and dialogue balance."""
    extractor = LectureMetadataExtractor()

    transcripts = [
        TranscriptSegmentItem(start_time=0.0, end_time=30.0, speaker="Teacher", text="This is a test speech segment with twenty five words to evaluate the academic speaking pace and words per minute calculations in real time."),
        TranscriptSegmentItem(start_time=30.0, end_time=60.0, speaker="Student", text="Thank you professor, the pace is very clear and understandable."),
    ]

    video_summary = VideoIntelligenceSummary(
        total_duration_sec=60.0,
        analyzed_frames_count=12,
        teacher_presence_ratio=0.85,
        board_writing_ratio=0.40,
        ppt_presentation_ratio=0.35,
        student_interaction_ratio=0.15,
        total_scene_changes=2,
    )

    metadata = extractor.extract_metadata(
        transcript_segments=transcripts,
        topic_segments=[],
        video_summary=video_summary,
        total_duration_sec=60.0,
    )

    assert metadata.total_words > 0
    assert metadata.words_per_minute > 0
    assert metadata.pace_rating in {"OPTIMAL", "SLOW", "RUSHED"}
    assert metadata.teacher_talk_ratio > 0.5
    assert metadata.student_talk_ratio > 0.0
    assert metadata.board_writing_ratio == 0.40
    assert metadata.slide_presentation_ratio == 0.35
    assert metadata.sync_quality_score >= 0.95


def test_lecture_structuring_service_and_api(tmp_path):
    """Integration test: Process structuring via REST API."""
    session_id = uuid4()
    req_payload = {
        "min_topic_duration_sec": 10.0,
        "sync_resolution_sec": 5.0,
        "auto_persist_db": False,
    }

    res = client.post(f"/api/v1/structuring/process/{session_id}", json=req_payload)
    assert res.status_code == 200, res.text

    data = res.json().get("data", res.json())
    assert data["session_id"] == str(session_id)
    assert data["status"] == "STRUCTURED"
    assert "metadata" in data
    assert "topic_segments" in data
    assert "synchronized_timeline" in data

    # Test GET endpoints
    res_struct = client.get(f"/api/v1/structuring/structured-lecture/{session_id}")
    assert res_struct.status_code == 200

    res_sync = client.get(f"/api/v1/structuring/sync-timeline/{session_id}")
    assert res_sync.status_code == 200
    sync_list = res_sync.json().get("data", res_sync.json())
    assert len(sync_list) >= 1

    res_topics = client.get(f"/api/v1/structuring/topic-segments/{session_id}")
    assert res_topics.status_code == 200
    topic_list = res_topics.json().get("data", res_topics.json())
    assert len(topic_list) >= 1
