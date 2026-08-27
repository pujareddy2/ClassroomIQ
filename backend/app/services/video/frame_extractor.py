"""
Frame Extractor & OpenCV Video Ingestion Pipeline.
Handles video frame extraction, temporal downsampling, keyframe saving, and scene change detection.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FrameExtractor:
    """Extracts frames from video files with timestamp tracking and scene transition metrics."""

    def __init__(self, target_width: int = 1280, target_height: int = 720):
        self.target_width = target_width
        self.target_height = target_height

    def extract_sampled_frames(
        self,
        video_path: Path,
        sample_interval_sec: float = 5.0,
        max_frames: int = 100,
    ) -> List[Tuple[float, np.ndarray]]:
        """
        Extracts frames at regular time intervals.
        Returns a list of (timestamp_sec, frame_bgr_image) tuples.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error("Could not open video with OpenCV: %s", video_path)
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_sec = total_frames / fps if fps > 0 else 0.0

        interval_frames = max(1, int(fps * sample_interval_sec))
        sampled_results: List[Tuple[float, np.ndarray]] = []

        current_frame_idx = 0
        frame_counter = 0

        while current_frame_idx < total_frames and frame_counter < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            timestamp_sec = round(current_frame_idx / fps, 2)

            # Resize to standardized processing resolution if needed
            if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
                processed_frame = cv2.resize(frame, (self.target_width, self.target_height))
            else:
                processed_frame = frame

            sampled_results.append((timestamp_sec, processed_frame))
            frame_counter += 1
            current_frame_idx += interval_frames

        cap.release()
        logger.info(
            "Extracted %d sampled frames from video %s (duration: %.1fs, fps: %.1f)",
            len(sampled_results),
            video_path.name,
            duration_sec,
            fps,
        )
        return sampled_results

    def compute_scene_change_score(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        Calculates difference metric (0.0 - 1.0) between consecutive frames using HSV histogram correlation.
        A score closer to 1.0 indicates high difference (scene change / slide transition).
        """
        if prev_frame is None or curr_frame is None:
            return 1.0

        # Convert to HSV and calculate Hue-Saturation histogram
        hsv_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2HSV)
        hsv_curr = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2HSV)

        hist_prev = cv2.calcHist([hsv_prev], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist_curr = cv2.calcHist([hsv_curr], [0, 1], None, [50, 60], [0, 180, 0, 256])

        cv2.normalize(hist_prev, hist_prev, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist_curr, hist_curr, 0, 1, cv2.NORM_MINMAX)

        # Correlation returns 1.0 for identical, -1.0 for completely different
        similarity = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CORREL)
        difference = max(0.0, min(1.0, 1.0 - max(0.0, similarity)))
        return round(float(difference), 3)

    def save_keyframe(
        self,
        frame: np.ndarray,
        output_dir: Path,
        filename: str,
        jpeg_quality: int = 85,
    ) -> Path:
        """Saves a frame as a JPEG image in the target directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / filename
        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        return out_path
