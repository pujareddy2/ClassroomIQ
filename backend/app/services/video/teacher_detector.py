"""
Teacher & Instructor Detection Engine.
Detects human presence, spatial bounding box coordinates, and classroom zone tracking.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.schemas.video import DetectionBox

logger = logging.getLogger(__name__)


class TeacherDetector:
    """Detects instructor presence, bounding boxes, and stage location zones."""

    def __init__(self):
        # Initialize OpenCV Default HOG Person Detector if available
        self.hog = None
        try:
            if hasattr(cv2, "HOGDescriptor"):
                self.hog = cv2.HOGDescriptor()
                if hasattr(cv2, "HOGDescriptor_getDefaultPeopleDetector"):
                    self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        except Exception as e:
            logger.debug("HOGDescriptor initialization failed: %s", e)

    def detect_teacher(self, frame: np.ndarray) -> Tuple[bool, Optional[DetectionBox], Optional[str]]:
        """
        Detects if an instructor is visible in the frame.
        Returns:
            (is_detected, DetectionBox, zone_name)
        """
        if frame is None or frame.size == 0:
            return False, None, None

        height, width = frame.shape[:2]
        detected_box: Optional[DetectionBox] = None
        best_conf = 0.0

        # 1. Try HOG person detection if available
        if self.hog is not None:
            try:
                boxes, weights = self.hog.detectMultiScale(
                    frame,
                    winStride=(8, 8),
                    padding=(16, 16),
                    scale=1.05,
                )
                if len(boxes) > 0:
                    for (x, y, w, h), weight in zip(boxes, weights):
                        area_ratio = (w * h) / (width * height)
                        if area_ratio < 0.015:
                            continue
                        conf = float(min(0.98, max(0.60, float(weight) if isinstance(weight, (int, float, np.floating)) else 0.85)))
                        if conf > best_conf:
                            best_conf = conf
                            detected_box = DetectionBox(
                                x=int(x),
                                y=int(y),
                                w=int(w),
                                h=int(h),
                                confidence=round(conf, 2),
                                label="teacher",
                                zone=self._determine_zone(int(x), int(w), width),
                            )
            except Exception as exc:
                logger.debug("HOG detectMultiScale error: %s", exc)

        # 2. Fallback heuristic: Contour saliency in upper/middle stage if HOG misses
        if detected_box is None:
            detected_box = self._detect_via_saliency(frame, width, height)

        if detected_box is not None:
            return True, detected_box, detected_box.zone

        return False, None, None

    def _determine_zone(self, x: int, w: int, frame_width: int) -> str:
        """Categorizes teacher position into classroom stage zones."""
        center_x = x + (w / 2)
        ratio = center_x / float(frame_width)

        if ratio < 0.33:
            return "board_left"
        elif ratio > 0.67:
            return "board_right"
        elif 0.33 <= ratio <= 0.45:
            return "podium"
        else:
            return "center"

    def _detect_via_saliency(self, frame: np.ndarray, width: int, height: int) -> Optional[DetectionBox]:
        """Secondary heuristic detector based on upper-body foreground contrast."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)
            # Threshold to isolate foreground elements
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = h / float(w) if w > 0 else 0
                area_ratio = (w * h) / float(width * height)

                # Human standing/sitting aspect ratio is typically between 1.2 and 3.5
                if 1.2 <= aspect_ratio <= 3.8 and 0.03 <= area_ratio <= 0.45:
                    return DetectionBox(
                        x=int(x),
                        y=int(y),
                        w=int(w),
                        h=int(h),
                        confidence=0.72,
                        label="teacher",
                        zone=self._determine_zone(int(x), int(w), width),
                    )
        except Exception as e:
            logger.debug("Saliency detection fallback failed: %s", e)

        return None
