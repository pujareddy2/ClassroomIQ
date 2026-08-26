"""
Multi-Track Media Synchronizer Engine.
Aligns speech transcript segments, visual scenes, and slide deck presentations on a unified timeline.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.schemas.audio import TranscriptSegmentItem
from app.schemas.structuring import SyncPoint
from app.schemas.video import SceneType, VisualTimelineEvent

logger = logging.getLogger(__name__)


class MediaSynchronizer:
    """Synchronizes multi-modal streams (Audio Transcripts, Video Scenes, Slides) on a unified temporal timeline."""

    def build_synchronized_timeline(
        self,
        transcript_segments: List[TranscriptSegmentItem],
        visual_events: List[VisualTimelineEvent],
        slides: Optional[List[Dict[str, Any]]] = None,
        total_duration_sec: Optional[float] = None,
        resolution_sec: float = 2.0,
    ) -> List[SyncPoint]:
        """
        Creates a list of synchronized timeline checkpoints.
        """
        slides_list = slides or []

        # Determine total duration
        duration = total_duration_sec or 0.0
        if duration <= 0.0:
            if transcript_segments:
                duration = max(duration, transcript_segments[-1].end_sec)
            if visual_events:
                duration = max(duration, visual_events[-1].end_time_sec)
            if duration <= 0.0:
                duration = 30.0

        sync_points: List[SyncPoint] = []
        current_time = 0.0

        while current_time <= duration:
            t = round(current_time, 2)

            # 1. Match Active Spoken Segment
            active_text = None
            active_speaker = "Teacher"
            for seg in transcript_segments:
                if seg.start_sec <= t <= seg.end_sec:
                    active_text = seg.text
                    active_speaker = seg.speaker or "Teacher"
                    break

            # 2. Match Active Visual Scene
            active_scene = SceneType.TEACHER_LECTURING
            active_keyframe = None
            for evt in visual_events:
                if evt.start_time_sec <= t <= evt.end_time_sec:
                    active_scene = evt.scene_type
                    active_keyframe = evt.keyframe_url
                    break

            # 3. Match Active Slide
            active_slide_idx = None
            active_slide_title = None
            if slides_list:
                # If visual scene is PPT presentation or slides exist, estimate active slide
                slide_fraction = t / max(1.0, duration)
                slide_index = min(len(slides_list) - 1, int(slide_fraction * len(slides_list)))
                slide_obj = slides_list[slide_index]
                active_slide_idx = slide_obj.get("slide_number", slide_index + 1)
                active_slide_title = slide_obj.get("title", f"Slide {active_slide_idx}")

            sync_points.append(
                SyncPoint(
                    timestamp_sec=t,
                    speech_text=active_text,
                    speaker=active_speaker,
                    visual_scene=active_scene,
                    slide_number=active_slide_idx,
                    slide_title=active_slide_title,
                    keyframe_url=active_keyframe,
                )
            )

            current_time += resolution_sec

        logger.info(
            "Built %d multi-track synchronized checkpoints across %.1fs lecture",
            len(sync_points),
            duration,
        )
        return sync_points
