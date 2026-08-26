"""
Lecture Structuring & Multi-Modal Handover Services (Module 4).
"""

from app.services.structuring.lecture_metadata_extractor import LectureMetadataExtractor
from app.services.structuring.lecture_structuring_service import LectureStructuringService
from app.services.structuring.media_synchronizer import MediaSynchronizer
from app.services.structuring.topic_segmenter import TopicSegmenter

__all__ = [
    "LectureStructuringService",
    "MediaSynchronizer",
    "TopicSegmenter",
    "LectureMetadataExtractor",
]
