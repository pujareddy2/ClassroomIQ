"""
Pydantic schemas for the Video Intelligence & Computer Vision API (Module 3).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SceneType(str, Enum):
    TEACHER_LECTURING = "TEACHER_LECTURING"
    BOARD_WRITING = "BOARD_WRITING"
    PPT_PRESENTATION = "PPT_PRESENTATION"
    CLASSROOM_INTERACTION = "CLASSROOM_INTERACTION"
    UNKNOWN = "UNKNOWN"


class DetectionBox(BaseModel):
    x: int = Field(..., description="Top-left X pixel coordinate")
    y: int = Field(..., description="Top-left Y pixel coordinate")
    w: int = Field(..., description="Bounding box width")
    h: int = Field(..., description="Bounding box height")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    label: str = Field(default="person")
    zone: Optional[str] = Field(default=None, description="Spatial zone: podium, left, right, center")


class VideoFrameAnalysis(BaseModel):
    timestamp_sec: float
    scene_type: SceneType
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    teacher_detected: bool = False
    teacher_box: Optional[DetectionBox] = None
    teacher_zone: Optional[str] = None
    board_detected: bool = False
    board_box: Optional[DetectionBox] = None
    stroke_density: float = Field(default=0.0, description="Active chalk/marker stroke density percentage 0-100")
    ppt_detected: bool = False
    ppt_box: Optional[DetectionBox] = None
    slide_transition: bool = False
    keyframe_filename: Optional[str] = None


class VisualTimelineEvent(BaseModel):
    event_id: str
    start_time_sec: float
    end_time_sec: float
    duration_sec: float
    scene_type: SceneType
    label: str
    description: str
    keyframe_url: Optional[str] = None
    teacher_present: bool = True
    board_active: bool = False
    ppt_active: bool = False
    confidence: float = 0.85


class VideoIntelligenceSummary(BaseModel):
    total_duration_sec: float
    analyzed_frames_count: int
    teacher_presence_ratio: float = Field(..., ge=0.0, le=1.0, description="Fraction of lecture where teacher is in frame")
    board_writing_ratio: float = Field(..., ge=0.0, le=1.0, description="Fraction of lecture involving board writing")
    ppt_presentation_ratio: float = Field(..., ge=0.0, le=1.0, description="Fraction of lecture displaying digital slides")
    student_interaction_ratio: float = Field(..., ge=0.0, le=1.0, description="Fraction of lecture focusing on classroom / audience")
    total_scene_changes: int = 0
    average_confidence: float = 0.85
    timeline_events_count: int = 0


class VideoProcessRequest(BaseModel):
    sample_interval_sec: float = Field(default=5.0, ge=0.5, le=60.0, description="Sampling rate in seconds for frame analysis")
    detect_teacher: bool = True
    detect_board: bool = True
    detect_ppt: bool = True
    detect_gestures: bool = False
    min_scene_duration_sec: float = Field(default=3.0, ge=1.0, description="Minimum duration to cluster into a distinct scene event")


class VideoProcessResponse(BaseModel):
    session_id: UUID
    status: str
    summary: VideoIntelligenceSummary
    timeline: List[VisualTimelineEvent]
    keyframes: List[Dict[str, Any]]
    analyzed_at: str
