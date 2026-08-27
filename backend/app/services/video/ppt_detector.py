"""
Presentation Slide & Digital Screen Detection Engine.
Detects projector screens, digital PPT displays, slide regions, and slide transition events.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from app.schemas.video import DetectionBox

logger = logging.getLogger(__name__)


class PPTDetector:
    """Detects digital presentation slides, projector displays, and slide transition events."""

    def __init__(self, min_slide_area_ratio: float = 0.12):
        self.min_slide_area_ratio = min_slide_area_ratio
        self.last_slide_fingerprint: Optional[np.ndarray] = None

    def detect_ppt(self, frame: np.ndarray) -> Tuple[bool, Optional[DetectionBox], bool]:
        """
        Detects if a presentation slide / digital screen is active in the frame.
        Returns:
            (is_ppt_detected, DetectionBox, is_slide_transition)
        """
        if frame is None or frame.size == 0:
            return False, None, False

        height, width = frame.shape[:2]
        total_area = width * height

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Slides typically have high uniform background brightness or sharp borders
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_box: Optional[DetectionBox] = None
        best_area = 0.0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            area_ratio = area / float(total_area)
            aspect_ratio = w / float(h) if h > 0 else 0

            # Digital presentation screens typically follow 4:3 (1.33) or 16:9 (1.77) aspect ratio
            if area_ratio >= self.min_slide_area_ratio and 1.25 <= aspect_ratio <= 1.95:
                if area > best_area:
                    best_area = area
                    best_box = DetectionBox(
                        x=int(x),
                        y=int(y),
                        w=int(w),
                        h=int(h),
                        confidence=0.92,
                        label="ppt_screen",
                        zone="center" if x > width * 0.2 and (x + w) < width * 0.8 else "screen",
                    )

        is_transition = False
        if best_box is not None:
            # Check for slide transition
            crop = gray[best_box.y : best_box.y + best_box.h, best_box.x : best_box.x + best_box.w]
            resized_crop = cv2.resize(crop, (64, 36))

            if self.last_slide_fingerprint is not None:
                # Compare structural difference with previous slide crop
                diff = cv2.absdiff(self.last_slide_fingerprint, resized_crop)
                mean_diff = float(np.mean(diff))
                # High difference in PPT screen region indicates a new slide being displayed
                if mean_diff > 25.0:
                    is_transition = True

            self.last_slide_fingerprint = resized_crop
            return True, best_box, is_transition

        return False, None, False
