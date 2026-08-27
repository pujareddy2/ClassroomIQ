"""
Whiteboard & Blackboard Detection Engine.
Identifies physical teaching boards, boundaries, and computes active chalk/marker stroke writing density.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

from app.schemas.video import DetectionBox

logger = logging.getLogger(__name__)


class BoardDetector:
    """Detects teaching boards (Whiteboard / Blackboard) and estimates active stroke density."""

    def __init__(self, min_board_area_ratio: float = 0.08):
        self.min_board_area_ratio = min_board_area_ratio

    def detect_board(self, frame: np.ndarray) -> Tuple[bool, Optional[DetectionBox], float]:
        """
        Analyzes a video frame for teaching boards.
        Returns:
            (is_board_detected, DetectionBox, stroke_density_pct)
        """
        if frame is None or frame.size == 0:
            return False, None, 0.0

        height, width = frame.shape[:2]
        total_area = width * height

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 1. Edge & Quadrilateral Detection for large rectangular board structures
        edges = cv2.Canny(blurred, 40, 120)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        best_box: Optional[DetectionBox] = None
        best_area = 0.0
        best_stroke_density = 0.0

        for cnt in contours:
            perimeter = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.03 * perimeter, True)

            # Boards are generally convex quadrilaterals (4 vertices) or rectangular bounds
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            area_ratio = area / float(total_area)

            # Look for wide horizontal boards (aspect ratio width:height usually >= 1.2)
            aspect_ratio = w / float(h) if h > 0 else 0

            if area_ratio >= self.min_board_area_ratio and 1.1 <= aspect_ratio <= 4.0:
                if area > best_area:
                    # Crop board region and compute stroke writing density
                    board_crop = gray[y : y + h, x : x + w]
                    stroke_pct = self._calculate_stroke_density(board_crop)

                    # Check if it is blackboard (dark) or whiteboard (bright)
                    mean_val = float(np.mean(board_crop))
                    board_type = "blackboard" if mean_val < 110 else "whiteboard"

                    best_area = area
                    best_stroke_density = stroke_pct
                    best_box = DetectionBox(
                        x=int(x),
                        y=int(y),
                        w=int(w),
                        h=int(h),
                        confidence=0.88,
                        label=board_type,
                        zone="board_left" if (x + w / 2) < width * 0.5 else "board_right",
                    )

        if best_box is not None:
            return True, best_box, round(best_stroke_density, 2)

        # Fallback: Check if large portion of top-middle background acts as a teaching board
        fallback_stroke = self._calculate_stroke_density(gray[int(height * 0.1) : int(height * 0.7), int(width * 0.1) : int(width * 0.9)])
        if fallback_stroke > 1.5:
            fallback_box = DetectionBox(
                x=int(width * 0.1),
                y=int(height * 0.1),
                w=int(width * 0.8),
                h=int(height * 0.6),
                confidence=0.65,
                label="board",
                zone="center",
            )
            return True, fallback_box, round(fallback_stroke, 2)

        return False, None, 0.0

    def _calculate_stroke_density(self, board_gray: np.ndarray) -> float:
        """
        Calculates stroke writing density (percentage 0.0 - 100.0)
        using adaptive thresholding and morphological gradient.
        """
        if board_gray is None or board_gray.size == 0:
            return 0.0

        try:
            # Adaptive threshold isolates thin chalk/marker lines from illumination gradients
            adaptive = cv2.adaptiveThreshold(
                board_gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                15,
                4,
            )

            # Morphological noise removal
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            clean_strokes = cv2.morphologyEx(adaptive, cv2.MORPH_OPEN, kernel)

            stroke_pixels = np.count_nonzero(clean_strokes)
            total_pixels = clean_strokes.size

            stroke_density_pct = (stroke_pixels / float(total_pixels)) * 100.0
            return float(min(100.0, stroke_density_pct))
        except Exception as e:
            logger.debug("Stroke density calculation error: %s", e)
            return 0.0
