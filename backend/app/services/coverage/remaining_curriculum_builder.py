"""
Remaining Curriculum Builder component for Curriculum Coverage Intelligence Engine.
Generates remaining un-covered or partially covered units, chapters, topics, and learning outcomes.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set
from uuid import UUID

from app.services.coverage.coverage_models import CoverageStatus
from app.services.curriculum_hierarchy.hierarchy_models import CurriculumSegment

logger = logging.getLogger(__name__)


class RemainingCurriculumBuilder:
    """Computes remaining units, chapters, topics, and learning outcomes."""

    @staticmethod
    def build_remaining_curriculum(
        segments: List[CurriculumSegment],
        topic_status_map: Dict[UUID, CoverageStatus],
    ) -> Dict[str, List[dict]]:
        """
        Returns:
            {
               "remaining_topics": [...],
               "remaining_chapters": [...],
               "remaining_units": [...],
               "remaining_learning_outcomes": [...]
            }
        """
        covered_statuses = {CoverageStatus.COVERED, CoverageStatus.OVER_EXPLAINED, CoverageStatus.REPEATED}

        remaining_topics: List[dict] = []
        remaining_chapters_map: Dict[UUID, dict] = {}
        remaining_units_map: Dict[UUID, dict] = {}
        remaining_outcomes: Set[str] = set()

        for segment in segments:
            unit_id = segment.unit_id
            unit_title = segment.unit_title
            chapter_id = segment.chapter_id
            chapter_title = segment.chapter_title

            segment_has_uncovered = False

            for idx, topic_id in enumerate(segment.topic_ids):
                topic_title = segment.topic_titles[idx] if idx < len(segment.topic_titles) else f"Topic {idx+1}"
                status = topic_status_map.get(topic_id, CoverageStatus.SKIPPED)

                if status not in covered_statuses:
                    segment_has_uncovered = True
                    remaining_topics.append({
                        "topic_id": str(topic_id),
                        "topic_name": topic_title,
                        "unit_title": unit_title,
                        "chapter_title": chapter_title or "General",
                        "status": status.value,
                    })

            if segment_has_uncovered:
                if chapter_id and chapter_title and chapter_id not in remaining_chapters_map:
                    remaining_chapters_map[chapter_id] = {
                        "chapter_id": str(chapter_id),
                        "chapter_title": chapter_title,
                        "unit_title": unit_title,
                    }

                if unit_id not in remaining_units_map:
                    remaining_units_map[unit_id] = {
                        "unit_id": str(unit_id),
                        "unit_title": unit_title,
                    }

                for lo in segment.learning_outcomes:
                    remaining_outcomes.add(lo)

        return {
            "remaining_topics": remaining_topics,
            "remaining_chapters": list(remaining_chapters_map.values()),
            "remaining_units": list(remaining_units_map.values()),
            "remaining_learning_outcomes": sorted(list(remaining_outcomes)),
        }
