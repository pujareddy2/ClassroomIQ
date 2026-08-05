"""
Statistics calculator for curriculum hierarchy trees.
Counts strictly using node_type field.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set
from uuid import UUID

from app.models.topic import Topic
from app.services.curriculum_hierarchy.hierarchy_models import (
    CurriculumStatistics,
    NodeType,
    UnitNode,
)

logger = logging.getLogger(__name__)


class CurriculumStatisticsCalculator:
    """Calculates node counts strictly using the node_type field."""

    @staticmethod
    def calculate(
        topic_rows: List[Topic],
        units: List[UnitNode],
        warnings: List[str],
    ) -> CurriculumStatistics:
        unit_count = 0
        chapter_count = 0
        topic_count = 0
        outcome_count = 0

        # Helper mapping for legacy rows without node_type set
        topic_map: Dict[UUID, Topic] = {t.id: t for t in topic_rows}

        for t in topic_rows:
            raw_type = (t.node_type or "").upper().strip()
            if not raw_type:
                # Infer type only if DB node_type is missing
                if t.parent_topic_id is None:
                    raw_type = "UNIT"
                elif t.topic_name == "Learning Outcomes":
                    raw_type = "CHAPTER"
                else:
                    parent = topic_map.get(t.parent_topic_id)
                    if parent and parent.topic_name == "Learning Outcomes":
                        raw_type = "LEARNING_OUTCOME"
                    elif parent and parent.parent_topic_id is None:
                        raw_type = "CHAPTER"
                    else:
                        raw_type = "TOPIC"

            if raw_type == "UNIT":
                unit_count += 1
            elif raw_type == "CHAPTER":
                chapter_count += 1
            elif raw_type in ("TOPIC", "SUBTOPIC"):
                topic_count += 1
            elif raw_type == "LEARNING_OUTCOME":
                outcome_count += 1

        total_nodes = len(topic_rows)

        # Compute max tree depth in O(n)
        max_depth = 0
        for t in topic_rows:
            depth = 1
            curr: Topic | None = t
            visited: Set[UUID] = set()
            while curr is not None and curr.parent_topic_id is not None:
                if curr.id in visited:
                    break
                visited.add(curr.id)
                depth += 1
                curr = topic_map.get(curr.parent_topic_id)
            if depth > max_depth:
                max_depth = depth

        status = "VALID"
        if warnings:
            status = "WARNING"
        if total_nodes == 0:
            status = "INVALID"

        return CurriculumStatistics(
            units=unit_count,
            chapters=chapter_count,
            topics=topic_count,
            learning_outcomes=outcome_count,
            total_nodes=total_nodes,
            tree_depth=max_depth,
            validation_status=status,
            warnings=warnings,
        )
