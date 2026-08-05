"""
Segment builder for converting curriculum hierarchy into flat, logical learning segments.
Populates hierarchy_path dynamically in memory for RAG, Transcript Mapping, and Coverage.
"""

from __future__ import annotations

import logging
from typing import Dict, List
from uuid import UUID

from app.models.topic import Topic
from app.services.curriculum_hierarchy.hierarchy_models import (
    CurriculumSegment,
    UnitNode,
)
from app.services.curriculum_hierarchy.tree_builder import CurriculumTreeBuilder

logger = logging.getLogger(__name__)


class CurriculumSegmentBuilder:
    """Generates logical curriculum segments with dynamic in-memory hierarchy paths."""

    @staticmethod
    def build_segments(
        curriculum_id: UUID,
        units: List[UnitNode],
        topic_map: Dict[UUID, Topic] | None = None,
    ) -> List[CurriculumSegment]:
        """
        Builds a flat list of CurriculumSegment items.
        Each segment represents a Chapter or Unit section with its topics and learning outcomes.
        """
        segments: List[CurriculumSegment] = []
        display_order = 1

        for unit in units:
            if not unit.chapters:
                # Segment for Unit directly without Chapters
                path = [unit.title]
                segment = CurriculumSegment(
                    segment_id=f"SEG_{curriculum_id.hex[:8]}_{unit.id.hex[:4]}_root",
                    curriculum_id=curriculum_id,
                    unit_id=unit.id,
                    unit_title=unit.title,
                    chapter_id=None,
                    chapter_title=None,
                    topic_ids=[],
                    topic_titles=[],
                    learning_outcome_ids=[],
                    learning_outcomes=[],
                    display_order=display_order,
                    hierarchy_path=path,
                )
                segments.append(segment)
                display_order += 1
                continue

            for chapter in unit.chapters:
                topic_ids = [t.id for t in chapter.topics]
                topic_titles = [t.title for t in chapter.topics]

                path = [unit.title, chapter.title]

                segment = CurriculumSegment(
                    segment_id=f"SEG_{curriculum_id.hex[:8]}_{unit.id.hex[:4]}_{chapter.id.hex[:4]}",
                    curriculum_id=curriculum_id,
                    unit_id=unit.id,
                    unit_title=unit.title,
                    chapter_id=chapter.id,
                    chapter_title=chapter.title,
                    topic_ids=topic_ids,
                    topic_titles=topic_titles,
                    learning_outcome_ids=[],
                    learning_outcomes=list(chapter.learning_outcomes),
                    display_order=display_order,
                    hierarchy_path=path,
                )
                segments.append(segment)
                display_order += 1

        logger.info(
            "Generated %d curriculum segment(s) for curriculum ID: %s",
            len(segments),
            curriculum_id,
        )
        return segments
