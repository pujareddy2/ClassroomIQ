"""
Semantic Topic Segmenter & Chaptering Engine.
Segments continuous multi-modal lecture streams into structured chapter topics with titles, summaries, and key concepts.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Set

from app.schemas.audio import TranscriptSegmentItem
from app.schemas.structuring import TopicSegmentItem
from app.schemas.video import VisualTimelineEvent

logger = logging.getLogger(__name__)

# Heuristic topic transition trigger phrases commonly used by educators
TRANSITION_CUES = [
    r"\b(let'?s\s+move\s+on\s+to|next\s+topic|next\s+we\s+will|turning\s+our\s+attention\s+to)\b",
    r"\b(now\s+let'?s\s+discuss|now\s+we\s+turn\s+to|let'?s\s+look\s+at)\b",
    r"\b(today\s+we\s+will\s+cover|in\s+this\s+section|first\s+concept)\b",
    r"\b(to\s+summarize|in\s+conclusion|finally\s+we\s+have)\b",
    r"\b(let'?s\s+solve\s+an\s+example|here\s+is\s+a\s+problem|derivation\s+on\s+the\s+board)\b",
]


class TopicSegmenter:
    """Segments continuous multi-track lecture data into cohesive topic chapters with metadata."""

    def segment_lecture(
        self,
        transcript_segments: List[TranscriptSegmentItem],
        visual_events: Optional[List[VisualTimelineEvent]] = None,
        slides: Optional[List[Dict[str, Any]]] = None,
        min_segment_duration_sec: float = 15.0,
    ) -> List[TopicSegmentItem]:
        """
        Derives structured topic segments combining speech semantic flow, slide titles, and visual changes.
        """
        if not transcript_segments:
            # If no transcript, derive segments from visual timeline or slides
            return self._derive_from_visual_or_slides(visual_events or [], slides or [])

        topic_items: List[TopicSegmentItem] = []
        slides_list = slides or []
        vis_events = visual_events or []

        current_utterances: List[TranscriptSegmentItem] = []
        current_start = transcript_segments[0].start_sec

        for idx, seg in enumerate(transcript_segments):
            current_utterances.append(seg)
            current_duration = seg.end_sec - current_start

            is_transition = False
            # Check cue phrases in speech
            for pat in TRANSITION_CUES:
                if re.search(pat, seg.text, re.IGNORECASE):
                    is_transition = True
                    break

            # If duration threshold met and transition detected (or last segment)
            if (is_transition and current_duration >= min_segment_duration_sec) or idx == len(transcript_segments) - 1:
                topic_items.append(
                    self._build_segment_item(
                        utterances=current_utterances,
                        start_time=current_start,
                        end_time=seg.end_sec,
                        slides=slides_list,
                        visual_events=vis_events,
                    )
                )
                current_utterances = []
                if idx < len(transcript_segments) - 1:
                    current_start = transcript_segments[idx + 1].start_sec

        # Ensure at least one comprehensive topic if none formed
        if not topic_items and current_utterances:
            topic_items.append(
                self._build_segment_item(
                    utterances=current_utterances,
                    start_time=current_start,
                    end_time=current_utterances[-1].end_sec,
                    slides=slides_list,
                    visual_events=vis_events,
                )
            )

        logger.info("Generated %d structured topic segments for lecture", len(topic_items))
        return topic_items

    def _build_segment_item(
        self,
        utterances: List[TranscriptSegmentItem],
        start_time: float,
        end_time: float,
        slides: List[Dict[str, Any]],
        visual_events: List[VisualTimelineEvent],
    ) -> TopicSegmentItem:
        """Constructs a single TopicSegmentItem with title, summary, keywords, and dominant modality."""
        combined_text = " ".join(u.text for u in utterances).strip()
        duration = max(1.0, round(end_time - start_time, 2))

        # 1. Extract Key Concepts & Terminology
        keywords = self._extract_keywords(combined_text)

        # 2. Derive Title
        title = self._derive_title(utterances, slides, start_time, end_time, keywords)

        # 3. Derive Concise Summary
        summary = self._generate_summary(utterances, title)

        # 4. Find Associated Slides
        slide_nums: List[int] = []
        for s in slides:
            # If slide title or text matches keywords
            s_num = s.get("slide_number", 1)
            s_title = s.get("title", "")
            if any(k.lower() in s_title.lower() for k in keywords[:3]) and s_num not in slide_nums:
                slide_nums.append(s_num)

        # 5. Dominant Visual Modality & Primary Speaker
        dominant_mod = self._get_dominant_modality(visual_events, start_time, end_time)
        teacher_count = sum(1 for u in utterances if u.speaker == "Teacher")
        student_count = len(utterances) - teacher_count
        primary_speaker = "Teacher" if teacher_count >= student_count else "Student"

        return TopicSegmentItem(
            segment_id=f"top_{uuid.uuid4().hex[:8]}",
            title=title,
            summary=summary,
            start_time_sec=round(start_time, 2),
            end_time_sec=round(end_time, 2),
            duration_sec=duration,
            key_concepts=keywords[:6],
            primary_speaker=primary_speaker,
            dominant_modality=dominant_mod,
            utterance_count=len(utterances),
            slide_numbers=slide_nums,
        )

    def _derive_title(
        self,
        utterances: List[TranscriptSegmentItem],
        slides: List[Dict[str, Any]],
        start_time: float,
        end_time: float,
        keywords: List[str],
    ) -> str:
        """Derives an informative, academic chapter title."""
        # Try matching active slide title
        if slides:
            mid_time = (start_time + end_time) / 2.0
            slide_idx = min(len(slides) - 1, int((mid_time / max(1.0, end_time)) * len(slides)))
            cand_title = slides[slide_idx].get("title", "")
            if cand_title and not cand_title.startswith("Slide"):
                return cand_title

        # Try key phrase or first sentence snippet
        if keywords:
            if len(keywords) >= 2:
                return f"{keywords[0].title()} & {keywords[1].title()}"
            return f"Discussion on {keywords[0].title()}"

        if utterances:
            first_sent = utterances[0].text.split(".")[0].strip()
            if len(first_sent) > 5 and len(first_sent) < 60:
                return first_sent.capitalize()

        return f"Lecture Segment ({int(start_time)}s - {int(end_time)}s)"

    def _generate_summary(self, utterances: List[TranscriptSegmentItem], title: str) -> str:
        """Generates a concise 1-2 sentence overview of the topic section."""
        if not utterances:
            return f"Covers academic concepts related to {title}."

        first_utt = utterances[0].text.strip()
        last_utt = utterances[-1].text.strip()

        if len(utterances) == 1:
            return first_utt if len(first_utt) < 180 else f"{first_utt[:177]}..."

        summary_text = f"{first_utt.split('.')[0]}. Key focus revolves around {title.lower()}."
        return summary_text

    def _extract_keywords(self, text: str) -> List[str]:
        """Extracts technical terms and salient nouns from transcript text."""
        stopwords: Set[str] = {
            "the", "and", "this", "that", "with", "from", "for", "are", "was", "were",
            "have", "has", "had", "will", "would", "can", "could", "should", "what",
            "when", "where", "which", "why", "how", "all", "any", "both", "each", "few",
            "more", "most", "other", "some", "such", "than", "too", "very", "just",
            "today", "class", "lecture", "okay", "hello", "welcome", "please", "now",
        }

        # Extract words with 4+ characters
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        freq: Dict[str, int] = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda item: item[1], reverse=True)
        return [w.capitalize() for w, count in sorted_words if count >= 1][:8]

    def _get_dominant_modality(self, visual_events: List[VisualTimelineEvent], start_time: float, end_time: float) -> str:
        """Finds the primary visual scene active during this time window."""
        if not visual_events:
            return "TEACHER_LECTURING"

        durations: Dict[str, float] = {}
        for evt in visual_events:
            # Overlap interval calculation
            overlap_start = max(start_time, evt.start_time_sec)
            overlap_end = min(end_time, evt.end_time_sec)
            if overlap_end > overlap_start:
                scene_name = evt.scene_type.value if hasattr(evt.scene_type, "value") else str(evt.scene_type)
                durations[scene_name] = durations.get(scene_name, 0.0) + (overlap_end - overlap_start)

        if not durations:
            return "TEACHER_LECTURING"

        return max(durations.items(), key=lambda x: x[1])[0]

    def _derive_from_visual_or_slides(
        self,
        visual_events: List[VisualTimelineEvent],
        slides: List[Dict[str, Any]],
    ) -> List[TopicSegmentItem]:
        """Fallback when no audio transcript is present."""
        items: List[TopicSegmentItem] = []
        if slides:
            for idx, s in enumerate(slides, start=1):
                items.append(
                    TopicSegmentItem(
                        segment_id=f"top_slide_{idx}",
                        title=s.get("title", f"Slide {idx}"),
                        summary=s.get("text_content", "")[:120] or f"Presentation slide {idx}",
                        start_time_sec=float((idx - 1) * 30),
                        end_time_sec=float(idx * 30),
                        duration_sec=30.0,
                        key_concepts=[s.get("title", f"Concept {idx}")],
                        primary_speaker="Teacher",
                        dominant_modality="PPT_PRESENTATION",
                        utterance_count=1,
                        slide_numbers=[idx],
                    )
                )
        elif visual_events:
            for idx, evt in enumerate(visual_events, start=1):
                items.append(
                    TopicSegmentItem(
                        segment_id=f"top_vis_{idx}",
                        title=evt.label,
                        summary=evt.description,
                        start_time_sec=evt.start_time_sec,
                        end_time_sec=evt.end_time_sec,
                        duration_sec=evt.duration_sec,
                        key_concepts=[evt.label],
                        primary_speaker="Teacher",
                        dominant_modality=evt.scene_type.value if hasattr(evt.scene_type, "value") else str(evt.scene_type),
                        utterance_count=1,
                    )
                )

        if not items:
            items.append(
                TopicSegmentItem(
                    segment_id="top_initial_1",
                    title="Lecture Overview & Introduction",
                    summary="Introductory section covering core concepts and discussion topics.",
                    start_time_sec=0.0,
                    end_time_sec=60.0,
                    duration_sec=60.0,
                    key_concepts=["Introduction", "Lecture Overview"],
                    primary_speaker="Teacher",
                    dominant_modality="TEACHER_LECTURING",
                    utterance_count=1,
                    slide_numbers=[],
                )
            )

        return items

