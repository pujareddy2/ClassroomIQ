"""
Multimedia Intelligence & Lecture Capture Services (Module 1).
"""

from app.services.multimedia.capture_service import CaptureService
from app.services.multimedia.ffmpeg_processor import FFmpegProcessor
from app.services.multimedia.slide_processor import SlideProcessor
from app.services.multimedia.storage_service import MultimediaStorageService

__all__ = [
    "CaptureService",
    "FFmpegProcessor",
    "SlideProcessor",
    "MultimediaStorageService",
]
