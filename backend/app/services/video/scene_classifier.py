"""
Scene Classification & Visual Timeline Clustering Engine.
Combines teacher, board, and PPT detectors into structured scene states and contiguous lecture timeline intervals.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.schemas.video import (
    DetectionBox,
    SceneType,
    VideoFrameAnalysis,
    VisualTimelineEvent,
)

logger = logging.getLogger(__name__)


class SceneClassifier:
    """Classifies frame signals and aggregates them into high-level visual lecture timeline events."""

    def classify_frame(
        self,
        timestamp_sec: float,
        teacher_detected: bool,
        teacher_box: Optional[DetectionBox],
        teacher_zone: Optional[str],
        board_detected: bool,
        board_box: Optional[DetectionBox],
        stroke_density: float,
        ppt_detected: bool,
        ppt_box: Optional[DetectionBox],
        slide_transition: bool,
        keyframe_filename: Optional[str] = None,
    ) -> VideoFrameAnalysis:
        """Determines the instantaneous scene category for a single sampled frame."""

        scene_type = SceneType.TEACHER_LECTURING
        confidence = 0.85

        # 1. PPT Screen Dominance
        if ppt_detected and (not teacher_detected or (ppt_box and ppt_box.w * ppt_box.h > (board_box.w * board_box.h if board_box else 0))):
            scene_type = SceneType.PPT_PRESENTATION
            confidence = 0.92

        # 2. Board Writing Activity (Teacher at board with significant stroke writing activity)
        elif board_detected and stroke_density > 1.8:
            if teacher_detected and teacher_zone in {"board_left", "board_right", "center"}:
                scene_type = SceneType.BOARD_WRITING
                confidence = 0.90
            elif not ppt_detected:
                scene_type = SceneType.BOARD_WRITING
                confidence = 0.82

        # 3. Teacher Lecturing (Teacher standing/explaining)
        elif teacher_detected:
            scene_type = SceneType.TEACHER_LECTURING
            confidence = 0.88

        # 4. Audience / Classroom View
        elif not teacher_detected and not board_detected and not ppt_detected:
            scene_type = SceneType.CLASSROOM_INTERACTION
            confidence = 0.75

        return VideoFrameAnalysis(
            timestamp_sec=timestamp_sec,
            scene_type=scene_type,
            confidence=confidence,
            teacher_detected=teacher_detected,
            teacher_box=teacher_box,
            teacher_zone=teacher_zone,
            board_detected=board_detected,
            board_box=board_box,
            stroke_density=stroke_density,
            ppt_detected=ppt_detected,
            ppt_box=ppt_box,
            slide_transition=slide_transition,
            keyframe_filename=keyframe_filename,
        )

    def generate_timeline_events(
        self,
        frame_analyses: List[VideoFrameAnalysis],
        min_event_duration_sec: float = 3.0,
    ) -> List[VisualTimelineEvent]:
        """
        Clusters consecutive frame classifications into unified chronological timeline events.
        Smooths out single-frame blips.
        """
        if not frame_analyses:
            return []

        events: List[VisualTimelineEvent] = []
        current_type = frame_analyses[0].scene_type
        start_time = frame_analyses[0].timestamp_sec
        keyframe = frame_analyses[0].keyframe_filename
        has_teacher = frame_analyses[0].teacher_detected
        has_board = frame_analyses[0].board_detected
        has_ppt = frame_analyses[0].ppt_detected

        for i in range(1, len(frame_analyses)):
            fa = frame_analyses[i]
            # If scene type changed or at the end
            if fa.scene_type != current_type:
                duration = round(fa.timestamp_sec - start_time, 2)
                if duration >= min_event_duration_sec or not events:
                    events.append(
                        self._create_event(
                            start_time=start_time,
                            end_time=fa.timestamp_sec,
                            scene_type=current_type,
                            keyframe=keyframe,
                            teacher_present=has_teacher,
                            board_active=has_board,
                            ppt_active=has_ppt,
                        )
                    )
                    current_type = fa.scene_type
                    start_time = fa.timestamp_sec
                    keyframe = fa.keyframe_filename
                    has_teacher = fa.teacher_detected
                    has_board = fa.board_detected
                    has_ppt = fa.ppt_detected
            else:
                # Accumulate activity flags
                has_teacher = has_teacher or fa.teacher_detected
                has_board = has_board or fa.board_detected
                has_ppt = has_ppt or fa.ppt_detected
                if not keyframe and fa.keyframe_filename:
                    keyframe = fa.keyframe_filename

        # Flush final trailing event
        last_fa = frame_analyses[-1]
        final_end = last_fa.timestamp_sec + (frame_analyses[1].timestamp_sec - frame_analyses[0].timestamp_sec if len(frame_analyses) > 1 else 5.0)
        events.append(
            self._create_event(
                start_time=start_time,
                end_time=round(final_end, 2),
                scene_type=current_type,
                keyframe=keyframe,
                teacher_present=has_teacher,
                board_active=has_board,
                ppt_active=has_ppt,
            )
        )

        return events

    def _create_event(
        self,
        start_time: float,
        end_time: float,
        scene_type: SceneType,
        keyframe: Optional[str],
        teacher_present: bool,
        board_active: bool,
        ppt_active: bool,
    ) -> VisualTimelineEvent:
        """Helper to format a timeline event with human-readable descriptions."""
        labels = {
            SceneType.TEACHER_LECTURING: "Instructor Explanation",
            SceneType.BOARD_WRITING: "Active Board Work",
            SceneType.PPT_PRESENTATION: "Slide Presentation",
            SceneType.CLASSROOM_INTERACTION: "Classroom & Discussion View",
            SceneType.UNKNOWN: "Lecture Visual Transition",
        }
        descriptions = {
            SceneType.TEACHER_LECTURING: "The instructor is addressing the class from the podium/stage.",
            SceneType.BOARD_WRITING: "The instructor is solving problems or deriving concepts on the whiteboard/blackboard.",
            SceneType.PPT_PRESENTATION: "Digital slides or presentation deck are prominently displayed.",
            SceneType.CLASSROOM_INTERACTION: "Camera capturing classroom environment or student discussion.",
            SceneType.UNKNOWN: "Visual transition between teaching modalities.",
        }

        duration = max(1.0, round(end_time - start_time, 2))
        return VisualTimelineEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            start_time_sec=round(start_time, 2),
            end_time_sec=round(end_time, 2),
            duration_sec=duration,
            scene_type=scene_type,
            label=labels.get(scene_type, "Visual Segment"),
            description=descriptions.get(scene_type, ""),
            keyframe_url=keyframe,
            teacher_present=teacher_present,
            board_active=board_active,
            ppt_active=ppt_active,
            confidence=0.88,
        )
