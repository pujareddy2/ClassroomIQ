"""
Video Intelligence & Computer Vision Processing Services (Module 3).
"""

from app.services.video.board_detector import BoardDetector
from app.services.video.frame_extractor import FrameExtractor
from app.services.video.ppt_detector import PPTDetector
from app.services.video.scene_classifier import SceneClassifier
from app.services.video.teacher_detector import TeacherDetector
from app.services.video.video_intelligence_service import VideoIntelligenceService

__all__ = [
    "VideoIntelligenceService",
    "FrameExtractor",
    "TeacherDetector",
    "BoardDetector",
    "PPTDetector",
    "SceneClassifier",
]
