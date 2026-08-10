"""
Topic Matcher component for Technical Validation Engine.
Deterministically maps a transcript chunk to the best matching curriculum segment/topic.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple
from uuid import UUID

from app.services.curriculum_hierarchy.hierarchy_models import CurriculumSegment

logger = logging.getLogger(__name__)

ENGLISH_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "against", "between", "into", "throughout",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "can", "could", "should", "would", "will",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return {w for w in words if w not in ENGLISH_STOPWORDS and len(w) > 2}


class TopicMatcher:
    """Matches a transcript chunk text to the best curriculum segment and specific topic ID."""

    @staticmethod
    def match_chunk_to_segment(
        chunk_text: str,
        segments: List[CurriculumSegment],
    ) -> Tuple[Optional[CurriculumSegment], Optional[UUID], str, float]:
        """
        Returns:
            (best_segment, best_topic_id, best_topic_name, match_confidence)
        """
        if not segments or not chunk_text.strip():
            return None, None, "General", 0.0

        chunk_tokens = _tokenize(chunk_text)
        if not chunk_tokens:
            return None, None, "General", 0.0

        best_segment: Optional[CurriculumSegment] = None
        best_topic_id: Optional[UUID] = None
        best_topic_name: str = "General"
        highest_score: float = 0.0

        for segment in segments:
            # 1. Exact title check in chunk_text
            for idx, topic_title in enumerate(segment.topic_titles):
                if topic_title.lower() in chunk_text.lower():
                    t_id = segment.topic_ids[idx] if idx < len(segment.topic_ids) else segment.unit_id
                    return segment, t_id, topic_title, 0.95

            # 2. Token overlap matching
            segment_text = f"{segment.unit_title} {segment.chapter_title or ''} {' '.join(segment.topic_titles)} {' '.join(segment.learning_outcomes)}"
            segment_tokens = _tokenize(segment_text)

            if not segment_tokens:
                continue

            overlap = chunk_tokens.intersection(segment_tokens)
            if not overlap:
                continue

            jaccard = len(overlap) / float(len(chunk_tokens.union(segment_tokens)))
            # Containment score
            containment = len(overlap) / float(min(len(chunk_tokens), len(segment_tokens)))
            score = 0.4 * jaccard + 0.6 * containment

            if score > highest_score:
                highest_score = score
                best_segment = segment
                if segment.topic_ids:
                    best_topic_id = segment.topic_ids[0]
                    best_topic_name = segment.topic_titles[0]
                else:
                    best_topic_id = segment.unit_id
                    best_topic_name = segment.unit_title

        if best_segment and highest_score >= 0.15:
            return best_segment, best_topic_id, best_topic_name, round(highest_score, 3)

        # Default fallback
        if segments:
            first_seg = segments[0]
            t_id = first_seg.topic_ids[0] if first_seg.topic_ids else first_seg.unit_id
            t_name = first_seg.topic_titles[0] if first_seg.topic_titles else first_seg.unit_title
            return first_seg, t_id, t_name, 0.10

        return None, None, "General", 0.0
